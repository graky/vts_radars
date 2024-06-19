import random
from typing import Any, Dict
from math_module import move_towards_destination, generate_random_point_inside_polygon, select_random_vertex
from shapely.geometry import Point
from static import NOVOROSSIYSK_VTS_POLYGON
import numpy as np
from sqlalchemy.orm import Session
from models import Ship as ShipModel, VTS as VTSModel, WeatherCondition as WeatherConditionModel, CoefficientDictionary
from dataclasses import  asdict
from db import SessionLocal


class WeatherCondition:
    def __init__(self, rain_rate: float = 0.0, visibility: float = 0.0, temperature: float = 20.0, humidity: float = 80.0, hail_diameter: float = 0.0) -> None:
        self.rain_rate = rain_rate
        self.visibility = visibility
        self.temperature = temperature
        self.humidity = humidity
        self.hail_diameter = hail_diameter

    @classmethod
    def load_from_db(cls, db: Session, weather_condition):
        if weather_condition is not None:
            with db:
                return cls(**asdict(db.query(WeatherConditionModel).filter(WeatherConditionModel.id==weather_condition.get("id")).first()))
        return None


class Ship:
    def __init__(self, name: str, nationality: str, length: float, width: float, bearing: float, speed: float, latitude: float=None, longitude: float=None, destination_latitude: float=None, destination_longitude: float=None) -> None:
        self.name = name
        self.nationality = nationality
        self.latitude = latitude
        self.longitude = longitude
        self.destination_latitude = destination_latitude
        self.destination_longitude = destination_longitude
        self.length = length
        self.width = width
        self.bearing = bearing
        self.speed = speed

    def start_positions(self):
        center = random.choice([(44.668781, 37.655415), (44.626849, 37.909026), (44.681143, 37.879564)])
        center = Point(center[0], center[1])
        ship_start_point = generate_random_point_inside_polygon(NOVOROSSIYSK_VTS_POLYGON, center=center)
        self.latitude, self.longitude = ship_start_point.x, ship_start_point.y
        ship_dest_point = select_random_vertex(NOVOROSSIYSK_VTS_POLYGON)
        self.destination_latitude, self.destination_longitude = ship_dest_point.x, ship_dest_point.y
        with SessionLocal() as session:
            db_ship = self.load_from_db_by_name(name=self.name)
            db_ship.latitude = self.latitude
            db_ship.longitude = self.longitude
            db_ship.destination_latitude = self.destination_latitude
            db_ship.destination_longitude = self.destination_longitude
            session.add(db_ship)
            session.commit()


    def update_position(self) -> None:
        new_cords = move_towards_destination(Point(self.latitude, self.longitude), Point(self.destination_latitude, self.destination_longitude), self.speed)
        self.latitude, self.longitude = new_cords.x, new_cords.y
        with SessionLocal() as session:
            db_ship = self.load_from_db_by_name(name=self.name)
            db_ship.latitude = self.latitude
            db_ship.longitude = self.longitude
            session.add(db_ship)
            session.commit()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "nationality": self.nationality,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "destination_latitude": self.destination_latitude,
            "destination_longitude": self.destination_longitude,
            "length": self.length,
            "width": self.width,
            "bearing": self.bearing,
            "speed": self.speed,
        }

    def save_to_db(self):
        with SessionLocal() as db:
            db_ship = ShipModel(
                name=self.name,
                nationality=self.nationality,
                length=self.length,
                width=self.width,
                bearing=self.bearing,
                speed=self.speed,
                latitude=self.latitude,
                longitude=self.longitude,
                destination_latitude=self.destination_latitude,
                destination_longitude=self.destination_longitude
            )
            db.add(db_ship)
            db.commit()
            db.refresh(db_ship)

    @classmethod
    def load_from_db(cls):
        with SessionLocal() as db:
            return [cls(**asdict(ship)) for ship in db.query(ShipModel).all()]

    @classmethod
    def load_from_db_by_name(cls, name):
        with SessionLocal() as db:
            return db.query(ShipModel).filter(ShipModel.name == name).first()
class VTS:
    def __init__(self, name: str, latitude: float, longitude: float, energy_potential: float, height: int, interference_multiplier:float, frequency: float, weather_condition: WeatherCondition) -> None:
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.energy_potential = energy_potential
        self.height = height
        self.interference_multiplier = interference_multiplier
        self.frequency = frequency
        self.weather_condition = weather_condition

    def calculate_S(self):
        # вычисления коэффициента затухания
        if self.weather_condition is None or (self.weather_condition.rain_rate== 0 and self.weather_condition.visibility == 0 and self.weather_condition.visibility > 10 and 50 <= self.weather_condition.humidity <= 80 and self.weather_condition.hail_diameter==0):
            return 0.01
        attenuation = 0
        with SessionLocal() as session:
            if self.weather_condition.rain_rate > 0:
                coefficients = session.query(CoefficientDictionary).filter(CoefficientDictionary.condition_type=="rain").first()
                k = coefficients.k
                b = coefficients.b
                attenuation += k * self.weather_condition.rain_rate ** b
            if self.weather_condition.visibility < 10:
                coefficients = session.query(CoefficientDictionary).filter(CoefficientDictionary.condition_type=="fog").first()
                visibility_factor = coefficients.visibility_factor
                attenuation += visibility_factor / self.weather_condition.visibility
            if self.weather_condition.hail_diameter > 0:
                coefficients = session.query(CoefficientDictionary).filter(CoefficientDictionary.condition_type=="hail").first()
                k_h = coefficients.k_h
                n = coefficients.n
                attenuation += k_h * self.weather_condition.hail_diameter ** n
        return attenuation


    def calculate_Dmax(self, sigma: float, D0: float) -> float:
        # вычисления эффективной дальности
        C = self.energy_potential
        F = self.interference_multiplier
        Dmax = (C * sigma) ** (1 / 4) * F * np.exp(-0.115 * self.calculate_S() * D0)
        return Dmax

    def save_to_db(self):
        with SessionLocal() as db:
            db_vts = VTSModel(
                name=self.name,
                latitude=self.latitude,
                longitude=self.longitude,
                energy_potential=self.energy_potential,
                height=self.height,
                interference_multiplier=self.interference_multiplier,
                frequency=self.frequency
            )
            db.add(db_vts)
            db.commit()

            db.refresh(db_vts)

    @classmethod
    def load_from_db(cls):
        with SessionLocal() as db:
            vts_models = [asdict(vts_model) for vts_model in db.query(VTSModel).all()]
            for vts_model in vts_models:
                vts_model["weather_condition"] = WeatherCondition(**vts_model.get("weather_condition")) if vts_model.get("weather_condition") else None
            return [cls(**vts_model) for vts_model in vts_models]


