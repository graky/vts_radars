import os
import sys
import requests
from typing import List
from qtpy.QtWidgets import QApplication, QVBoxLayout, QWidget, QDialog, QLabel, QPushButton
from qtpy.QtCore import QTimer
from pyqtlet2 import L, MapWidget
from structures import VTS, Ship
from static import NOVOROSSIYSK_VTS_POLYGON_CORDS
import pandas as pd
from datetime import datetime
from math_module import calculate_bearing, calculate_distance, calculate_aspect_angle, calculate_distance_correction, get_paths_by_start_and_destination, scaf_clustering, plan_routes
from db import SessionLocal
class ShipInfoDialog(QDialog):
    def __init__(self, ship: Ship, parent=None):
        super().__init__(parent)
        self.ship=ship
        self.setWindowTitle(f'Information - {ship.name}')
        self.setGeometry(100, 100, 200, 100)
        layout = QVBoxLayout()
        self.layout = layout
        self.info_label = QLabel(self.format_info(ship))
        layout.addWidget(self.info_label)
        self.setLayout(layout)
        # Set plan route button
        self.plan_route_button = QPushButton("Plan route")
        self.plan_route_button.clicked.connect(self.plan_route)
        self.layout.addWidget(self.plan_route_button)


    def update_info(self, ship: Ship):
        self.info_label.setText(self.format_info(ship))

    def format_info(self, ship: Ship) -> str:
        return (f'Name: {ship.name}\n'
                f'Nationality: {ship.nationality}\n'
                f'Position: ({ship.latitude}, {ship.longitude})\n'
                f'Length: {ship.length}m\n'
                f'Width: {ship.width}m\n'
                f'Bearing: {ship.bearing}°\n'
                f'Speed: {ship.speed} knots\n'
                f'Destination: ({ship.destination_latitude}, {ship.destination_longitude})')


    def plan_route(self):
        ship_start_point = (self.ship.latitude, self.ship.longitude)
        ship_dest_point = (self.ship.destination_latitude, self.ship.destination_longitude)
        paths = get_paths_by_start_and_destination("ship_cords_log.csv", *ship_start_point, *ship_dest_point)
        labels = scaf_clustering(paths, n_clusters=2)
        route = plan_routes(paths, labels)
        planned_route_for_ship = route[0]
        path = L.polyline(planned_route_for_ship, {"color": "red"})
        self.parent().map.addLayer(path)

class VTSInfoDialog(QDialog):
    def __init__(self, vts: VTS, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Information - {vts.name}')
        self.setGeometry(100, 100, 300, 200)  # Updated size to accommodate more information
        layout = QVBoxLayout()
        info_label = QLabel(
            f'Name: {vts.name}\n'
            f'Position: ({vts.latitude}, {vts.longitude})\n'
            f'Energy Potential: {vts.energy_potential}\n'
            f'Height: {vts.height}m\n'
            f'Interference Multiplier: {vts.interference_multiplier}\n'
            f'Frequncy: {vts.frequency}\n'
            f'Weather condition: {vts.weather_condition.__dict__ if vts.weather_condition else "No condition"}'
        )
        layout.addWidget(info_label)
        self.setLayout(layout)

class MapWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set up the map widget
        self.mapWidget = MapWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.mapWidget)
        self.setLayout(self.layout)
        self.db = SessionLocal()
        # Set reload button
        self.reload_button = QPushButton("Reload Ships")
        self.reload_button.clicked.connect(self.reload_ships)
        self.layout.addWidget(self.reload_button)

        # Set up the map
        self.map = L.map(self.mapWidget)
        self.map.setView([44.5906, 37.8208], 10)
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)

        # Coordinates of the sea area polygon
        self.sea_area_coords = NOVOROSSIYSK_VTS_POLYGON_CORDS

        self.ships: List[Ship] = []
        self.vts_stations = VTS.load_from_db()

        self.ship_markers: List[L.marker] = []
        self.lines: List[L.polyline] = []

        # Path to the ferry icon
        self.icon_path = os.path.abspath('ferry.png')

        # Add sea area polygon
        self.add_sea_area_polygon()

        # Add initial markers
        self.add_vts_stations()

        # Fetch ships and set up markers
        self.fetch_ships()

        # Set up a timer to update the positions
        self.timer = QTimer(self)
        self.timer.setInterval(5000)  # Update every 5 seconds
        self.timer.timeout.connect(self.update_positions)
        self.timer.start()
        self.ship_info_dialogs = {}

        self.show()

    def reload_ships(self):
        self.fetch_ships(reload=True)

    def log_ship_data(self, ship: Ship) -> None:
        data = []
        true_bearing = calculate_bearing(ship.latitude, ship.longitude, ship.destination_latitude, ship.destination_longitude)
        for vts in self.vts_stations:
            bearing = calculate_bearing(vts.longitude, vts.latitude, ship.longitude, ship.latitude)
            aspect_angle = calculate_aspect_angle(bearing, true_bearing)

            distance = calculate_distance(vts.latitude, vts.longitude, ship.latitude, ship.longitude)
            effective_distance = vts.calculate_Dmax(sigma=1000, D0=distance)
            distance_correction = calculate_distance_correction(aspect_angle, ship.length/2, ship.width/2)
            data.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'ship_name': ship.name,
                'ship_latitude': ship.latitude,
                'ship_longitude': ship.longitude,
                'destination_latitude': ship.destination_latitude,
                'destination_longitude': ship.destination_longitude,
                'vts_name': vts.name,
                'vts_latitude': vts.latitude,
                'vts_longitude': vts.longitude,
                'bearing': bearing,
                'distance_km': distance,
                "distance_correction": distance_correction,
                "effective_distance": effective_distance
            })

        df = pd.DataFrame(data)
        df.to_csv('ship_data_log.csv', mode='a', header=not os.path.exists('ship_data_log.csv'), index=False)
    def fetch_ships(self, reload: bool = False, update: bool = True):
        params = {}
        if reload:
            params['reload'] = True
        response = requests.get("http://localhost:8000/ships", params=params)
        ships_data = response.json()
        self.ships = [Ship(**data) for data in ships_data]
        if not self.ship_markers:
            self.add_ships()


    def add_sea_area_polygon(self) -> None:
        polygon = L.polygon(self.sea_area_coords, {'color': 'blue', 'fillColor': 'blue', 'fillOpacity': 0.2})
        self.map.addLayer(polygon)

    def add_vts_stations(self) -> None:
        for vts in self.vts_stations:
            marker = L.marker([vts.latitude, vts.longitude])
            popup_content = f'<b>{vts.name}</b><br>Position: ({vts.latitude}, {vts.longitude})'
            marker.bindPopup(popup_content)
            marker.click.connect(lambda event, v=vts: self.show_vts_info_dialog(v))
            self.map.addLayer(marker)

    def add_ships(self) -> None:
        ship_icon = L.icon(self.icon_path)
        self.map.addLayer(ship_icon)

        for ship in self.ships:
            marker = L.marker([ship.latitude, ship.longitude])
            marker.setIcon(ship_icon)
            popup_content = f'<b>{ship.name}</b><br>Position: ({ship.latitude}, {ship.longitude})'
            marker.bindPopup(popup_content)
            marker.click.connect(lambda event, s=ship: self.show_ship_info_dialog(s))
            self.map.addLayer(marker)
            marker.setIcon(icon=ship_icon)
            self.ship_markers.append(marker)
            self.add_lines_to_vts(ship)


    def add_lines_to_vts(self, ship: Ship) -> None:
        for vts in self.vts_stations:
            distance = calculate_distance(vts.latitude, vts.longitude, ship.latitude, ship.longitude)
            effective_distance = vts.calculate_Dmax(sigma=1000, D0=distance)
            if distance < effective_distance:
                line = L.polyline([[vts.latitude, vts.longitude], [ship.latitude, ship.longitude]], {'color': 'green', 'weight': 2, 'opacity': 0.5})
                self.map.addLayer(line)
                self.lines.append(line)

    def update_positions(self) -> None:
        # Fetch updated positions
        self.fetch_ships()
        # Update ship positions
        for marker, ship in zip(self.ship_markers, self.ships):
            popup_content = f'<b>{ship.name}</b><br>Position: ({ship.latitude}, {ship.longitude})'
            marker.bindPopup(popup_content)
            marker.setLatLng([ship.latitude, ship.longitude])
            if ship.name in self.ship_info_dialogs:
                self.ship_info_dialogs[ship.name].update_info(ship)
            self.log_ship_data(ship)

        # Clear and re-add lines to VTS stations
        for line in self.lines:
            self.map.removeLayer(line)
        self.lines.clear()
        for ship in self.ships:
            self.add_lines_to_vts(ship)

    def show_ship_info_dialog(self, ship: Ship) -> None:
        if ship.name not in self.ship_info_dialogs:
            dialog = ShipInfoDialog(ship, self)
            self.ship_info_dialogs[ship.name] = dialog
        else:
            dialog = self.ship_info_dialogs[ship.name]
            dialog.update_info(ship)
        dialog.show()

    def show_vts_info_dialog(self, vts: VTS) -> None:
        dialog = VTSInfoDialog(vts, self)
        dialog.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = MapWindow()
    widget.show()
    sys.exit(app.exec_())
