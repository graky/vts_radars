import random
import numpy as np
from shapely.geometry import Point
from sklearn.cluster import SpectralClustering
import pandas as pd
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import matplotlib.pyplot as plt


def calculate_distance(lat1, lon1, lat2, lon2):
    # расстояние между координатами судна и постом СУДС
    R = 6371.0  # Earth radius in kilometers
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c
    return distance
def calculate_bearing(x_radar, y_radar, x_ship, y_ship):
    # пеленг судна
    bearing_rad = np.arctan2(y_ship - y_radar, x_ship - x_radar)
    bearing_deg = np.degrees(bearing_rad)
    bearing_deg = (bearing_deg + 360) % 360  # Normalize to [0, 360)
    return bearing_deg


def calculate_initial_compass_bearing(lat1, lon1, lat2, lon2):
    if (lat1 == lat2) and (lon1 == lon2):
        return 0

    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlon = lon2_rad - lon1_rad

    x = np.sin(dlon) * np.cos(lat2_rad)
    y = np.cos(lat1_rad) * np.sin(lat2_rad) - (np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon))

    initial_bearing = np.arctan2(x, y)

    initial_bearing = np.degrees(initial_bearing)

    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def calculate_aspect_angle(B_R_T, C_T):
    # вычисления курсового угла
    if B_R_T - C_T < 0:
        alpha = B_R_T - C_T + 180
    elif B_R_T - C_T == 0:
        alpha = 180
    elif B_R_T - C_T == -180:
        alpha = 0
    elif B_R_T - C_T > 0:
        alpha =  B_R_T- C_T - 180
    return abs(alpha)

def calculate_distance_correction(alpha, a, b):
    # вычисления коррекции расстояния
    alpha_rad = np.radians(alpha)
    if alpha == 0 or alpha == 180:
        d_p_P = a
    elif alpha > 0 and alpha <= 90:
        d_p_P = (a * b) / np.sqrt(b**2 * np.cos(alpha_rad)**2 + a**2 * np.sin(alpha_rad)**2)
    elif alpha == 90:
        d_p_P = b
    elif alpha > 90 and alpha < 180:
        beta = 180 - alpha
        beta_rad = np.radians(beta)
        d_p_P = b / np.sin(beta_rad)
    return d_p_P

def correct_radar_distances(d_R, d_p_P):
    # вычисление скорректированного расстояния
    return d_R + d_p_P


def is_point_in_polygon(point, polygon):
    return polygon.contains(point)


def generate_random_point_inside_polygon( polygon, center=Point((44.626849, 37.909026)), radius_in_km=3,):
    # функция, задающая начальные координаты судна
    radius_in_degrees = radius_in_km / 111  # Roughly convert km to degrees
    minx, miny = center.x - radius_in_degrees, center.y - radius_in_degrees
    maxx, maxy = center.x + radius_in_degrees, center.y + radius_in_degrees

    while True:
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(p):
            return p

def select_random_vertex(polygon, points=[(44.668781, 37.655415), (44.626849, 37.909026), (44.681143, 37.879564)], radius_in_km=3):
    # функция, задающая точку назначения судна
    selected_center = random.choice(points)
    return generate_random_point_inside_polygon(center=Point(selected_center[0], selected_center[1]), radius_in_km=radius_in_km, polygon=polygon)


def move_towards_destination(current_position, destination,  speed):
    # функция изменения координат судна
    speed_deg_per_sec = (speed * 0.514444) / 111139 * 5
    vector = np.array([destination.x - current_position.x, destination.y - current_position.y])
    distance = np.linalg.norm(vector)
    if distance < speed_deg_per_sec:
        return destination
    unit_vector = vector / distance
    new_position = np.array([current_position.x, current_position.y]) + unit_vector * speed_deg_per_sec
    return Point(new_position[0], new_position[1])


# def move_towards_destination(current_position, destination,  speed):
#     # функция изменения координат судна
#     speed_deg_per_sec = (speed * 0.514444) / 111139 / 3600 * 5 * 3600
#     vector = np.array([destination.x - current_position.x, destination.y - current_position.y])
#     distance = np.linalg.norm(vector)
#     if distance < speed_deg_per_sec:
#         return False, destination
#     unit_vector = vector / distance
#     new_position = np.array([current_position.x, current_position.y]) + unit_vector * speed_deg_per_sec
#     return True, Point(new_position[0], new_position[1])
# #
# #
# ship1_start_position = Point(44.64391135101016,37.66260747892848)
# ship1_dest_position = Point(44.626849,37.909026)
# flag = True
# from  datetime import datetime
# import pandas as pd
# import os
# while flag == True:
#     flag, ship1_start_position = move_towards_destination(ship1_start_position, ship1_dest_position, 25)
#     data = []
#     data.append({
#         'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         'ship_name': "Ship2_test_trajectory2",
#         'ship_latitude': ship1_start_position.x,
#         'ship_longitude': ship1_start_position.y,
#         'destination_latitude': ship1_dest_position.x,
#         'destination_longitude': ship1_dest_position.y,
#         'vts_name': "",
#         'vts_latitude': "",
#         'vts_longitude': "",
#         'bearing': "",
#         'distance_km': "",
#         "distance_correction": "",
#         "effective_distance": ""
#     })
#
#     df = pd.DataFrame(data)
#     df.to_csv('ship_data_log.csv', mode='a', header=not os.path.exists('ship_data_log.csv'), index=False)




def get_paths_by_start_and_destination(file_path, start_lat, start_long, dest_lat, dest_long, tolerance=1e-6):
    # Filter the DataFrame for the given start and destination points
    df = pd.read_csv(file_path)
    def is_close(a, b, tol=tolerance):
        return abs(a - b) <= tol

    # Filter the DataFrame for the given start and destination points using the tolerance
    filtered_data = df[df.apply(lambda row: is_close(row['ship_latitude'], start_lat) and
                                            is_close(row['ship_longitude'], start_long) and
                                            is_close(row['destination_latitude'], dest_lat) and
                                            is_close(row['destination_longitude'], dest_long), axis=1)]
    if filtered_data.empty:
        return None

    # Extract the path coordinates as a list of lists for each ship
    paths = []
    for ship_name in filtered_data['ship_name'].unique():
        # Get the full trajectory for the ship based on the ship's name
        ship_data = df[df['ship_name'] == ship_name]
        path_coords = ship_data[['ship_latitude', 'ship_longitude']].values.tolist()
        paths.append(path_coords)
    return paths


def calculate_dynamic_weight(i, j, TNm, TNn, Nm, Nn):
    """
    Calculate dynamic weights for AADTW based on usage counts of points.
    """
    Ni_j = (TNm[i, j] + TNn[i, j]) / 2
    weight = ((Nm + Nn) / (2 * max(Nm, Nn))) * Ni_j

    return weight

def aadtw(trajectory_m, trajectory_n):
    Nm, Nn = len(trajectory_m), len(trajectory_n)
    AD = np.full((Nm, Nn), np.inf)
    TNm = np.zeros((Nm, Nn), dtype=int)
    TNn = np.zeros((Nm, Nn), dtype=int)

    AD[0, 0] = euclidean(trajectory_m[0], trajectory_n[0])
    TNm[0, 0] = TNn[0, 0] = 1  # Initialize usage counts at start point

    # Fill in the first row and column
    for i in range(1, Nm):
        AD[i, 0] = euclidean(trajectory_m[i], trajectory_n[0]) + AD[i - 1, 0]
        TNm[i, 0] = TNm[i - 1, 0] + 1
        TNn[i, 0] = 1

    for j in range(1, Nn):
        AD[0, j] = euclidean(trajectory_m[0], trajectory_n[j]) + AD[0, j - 1]
        TNm[0, j] = 1
        TNn[0, j] = TNn[0, j - 1] + 1

    # Fill in the rest of the matrix
    for i in range(1, Nm):
        for j in range(1, Nn):
            weighti1j = calculate_dynamic_weight(i-1, j, TNm, TNn, Nm, Nn)
            weightij1 = calculate_dynamic_weight(i, j-1, TNm, TNn, Nm, Nn)
            dist = euclidean(trajectory_m[i], trajectory_n[j])

            # Use the weight to adjust the computed distances
            AD1 = weighti1j * dist + dist + AD[i - 1, j]
            AD2 = dist + AD[i - 1, j-1]
            AD3 = weightij1 * dist + dist + AD[i, j-1]

            AD[i, j] = min(AD1, AD2, AD3)
            # Update the usage matrices based on which path was chosen
            if AD[i, j] == AD1:
                TNm[i, j] = 1
                TNn[i, j] = TNn[i - 1, j] + 1
            elif AD[i, j] == AD2:
                TNm[i, j] = 1
                TNn[i, j] = 1
            else:
                TNm[i, j] = TNm[i, j - 1] + 1
                TNn[i, j] = 1

    return AD[-1, -1]

def scaf_clustering(trajectories, n_clusters=2):
    n = len(trajectories)
    similarity_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(i, n):
            similarity_matrix[i][j] = similarity_matrix[j][i] = aadtw(trajectories[i], trajectories[j])
    sc = SpectralClustering(n_clusters=n_clusters, affinity='precomputed')
    labels = sc.fit_predict(similarity_matrix)
    return labels

def plan_routes(trajectories, labels):
    planned_routes = []

    for cluster_label in set(labels):
        cluster_trajectories = [trajectories[i] for i in range(len(trajectories)) if labels[i] == cluster_label]
        AD = np.zeros((len(cluster_trajectories), len(cluster_trajectories)))

        for m in range(len(cluster_trajectories)):
            for n in range(len(cluster_trajectories)):
                AD[m, n] = aadtw(cluster_trajectories[m], cluster_trajectories[n])

        f = np.sum(AD, axis=1)
        min_index = np.argmin(f)
        planned_route = cluster_trajectories[min_index]
        planned_routes.append(planned_route)

    return planned_routes

def plot_paths_and_planned_route(trajectories, planned_routes):
    plt.figure(figsize=(12, 8))

    # Plot original trajectories
    colors = ['yellow', 'red', 'blue', 'green', 'purple']
    for trajectory, color in zip(trajectories, colors):
        x, y = zip(*trajectory)
        plt.plot(x, y, marker='o', label=f'{color.capitalize()} Path', color=color)

#    Plot planned routes
    for planned_route in planned_routes:
        planned_x, planned_y = zip(*planned_route)
        plt.plot(planned_x, planned_y, label='Planned Route', color='black', marker='o', linestyle='--')

    plt.title('Paths and Planned Route')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.legend()
    plt.grid(True)
    plt.show()

# yellow_path = [
#     (1, 1), (1, 2), (1, 3), (1, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (3, 9),
#     (3, 10), (3, 11), (3, 12), (3, 13), (4, 13), (4, 14), (4, 15), (4, 16), (4, 17),
#     (5, 17), (6, 17), (7, 17), (7, 18), (8, 18), (9, 19), (10, 20)
# ]
#
# red_path = [
#     (1, 1), (2, 1), (3, 1), (4, 2), (5, 3), (6, 5), (6, 6), (6, 7), (6, 8), (6, 9),
#     (7, 9), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14), (8, 15), (9, 16),
#     (10, 16), (10, 17), (10, 18), (10, 19), (10, 20)
# ]
#
# blue_path = [
#     (1, 1), (1, 2), (1, 3), (2, 3), (2, 4), (2, 5), (3, 5), (3, 6), (3, 7), (4, 7),
#     (4, 8), (4, 9), (5, 9), (5, 10), (5, 11), (6, 11), (6, 12), (7, 12), (7, 13),
#     (8, 13), (8, 14), (8, 15), (9, 15), (9, 16), (10, 17), (10, 18), (10, 19), (10, 20)
# ]
#
# green_path = [
#     (1, 1), (1, 2), (2, 2), (2, 3), (2, 4), (3, 4), (3, 5), (4, 5), (4, 6), (4, 7),
#     (5, 7), (5, 8), (5, 9), (6, 9), (6, 10), (6, 11), (7, 11), (7, 12), (8, 12),
#     (8, 13), (8, 14), (9, 14), (9, 15), (9, 16), (10, 16), (10, 17), (10, 18), (10, 19), (10, 20)
# ]
#
# purple_path = [
#     (1, 1), (1, 2), (2, 2), (2, 3), (2, 4), (3, 4), (3, 5), (3, 6), (4, 6), (4, 7),
#     (4, 8), (5, 8), (5, 9), (5, 10), (6, 10), (6, 11), (7, 11), (7, 12), (8, 12),
#     (8, 13), (8, 14), (9, 14), (9, 15), (10, 15), (10, 16), (10, 17), (10, 18), (10, 19), (10, 20)
# ]
#
# # Generate sample data
# trajectories = [yellow_path, red_path, blue_path, green_path, purple_path]
#
# # Run clustering and pathfinding
# labels = scaf_clustering(trajectories, n_clusters=1)
# planned_routes = plan_routes(trajectories, labels)
#
# # Plot paths and planned route
# plot_paths_and_planned_route(trajectories, planned_routes)