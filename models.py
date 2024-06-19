from sqlalchemy import Column, Integer, String, Float, ForeignKey
from db import Base, admin, SessionLocal, engine
from starlette_admin.contrib.sqla import ModelView
from dataclasses import dataclass
from sqlalchemy.orm import  relationship, mapped_column, Mapped
from typing import List

@dataclass
class Ship(Base):
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, index=True)
    nationality: str = Column(String)
    length: float = Column(Float)
    width: float = Column(Float)
    bearing: float = Column(Float)
    speed: float = Column(Float)
    latitude: float = Column(Float)
    longitude: float = Column(Float)
    destination_latitude: float = Column(Float)
    destination_longitude: float = Column(Float)


@dataclass
class WeatherCondition(Base):
    __tablename__ = 'weather_conditions'
    id = Column(Integer, primary_key=True)
    rain_rate: float = Column(Float, nullable=False, default=0.0)
    visibility: float = Column(Float, nullable=False, default=0.0)
    temperature: float = Column(Float, nullable=False, default=20.0)
    humidity: float = Column(Float, nullable=False, default=80.0)
    hail_diameter: float = Column(Float, nullable=False, default=0.0)


@dataclass
class VTS(Base):
    __tablename__ = "vts_stations"

    id = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, index=True)
    latitude: float = Column(Float)
    longitude: float = Column(Float)
    energy_potential: float = Column(Float)
    height: int = Column(Integer)
    interference_multiplier: float = Column(Float)
    frequency: float = Column(Float, nullable=False, default=1.0)
    weather_condition_id = mapped_column(ForeignKey("weather_conditions.id",  ondelete='NO ACTION', ), nullable=True)
    weather_condition: Mapped[List["WeatherCondition"]] = relationship(backref="weather_conditions")


class CoefficientDictionary(Base):
    __tablename__ = 'coefficients'
    id = Column(Integer, primary_key=True)
    condition_type = Column(String, nullable=False)  # e.g., 'rain', 'hail', 'fog'
    k = Column(Float)
    b = Column(Float)
    k_h = Column(Float)
    n = Column(Float)
    visibility_factor = Column(Float)


# VTS_LIST = [
#             VTS(name='БРЛС Южная Озереевка', latitude=44.668781, longitude=37.655415, energy_potential=170.2, height=18, interference_multiplier=1.32, frequency=1),
#             VTS(name='БРЛС Дооб', latitude=44.626849, longitude=37.909026, energy_potential=152.8, height=22, interference_multiplier=1.62, frequency=1),
#             VTS(name='БРЛС Пенай', latitude=44.681143, longitude=37.879564, energy_potential=102.1, height=25, interference_multiplier=1.42, frequency=1)
#         ]
# with SessionLocal() as session:
#     for vts in VTS_LIST:
#         session.add(vts)
#         session.commit()
# rain_coeff = CoefficientDictionary(condition_type='rain', k=0.0001, b=0.8)
# hail_coeff = CoefficientDictionary(condition_type='hail', k_h=0.1, n=1.2)
# fog_coeff = CoefficientDictionary(condition_type='fog', visibility_factor=1)
# with SessionLocal() as session:
#     session.add_all([rain_coeff, hail_coeff, fog_coeff])
#     session.commit()
# with SessionLocal() as session:
#     rainy_weather = WeatherCondition(rain_rate=20, visibility=10, temperature=20, humidity=80, hail_diameter=0)
#     session.add(rainy_weather)
#     session.commit()
#
#     # Add a foggy weather condition to the database
#     foggy_weather = WeatherCondition(rain_rate=0, visibility=0.5, temperature=10, humidity=90, hail_diameter=0)
#     session.add(foggy_weather)
#     session.commit()

#Base.metadata.create_all(bind=engine)

admin.add_view(ModelView(Ship))
admin.add_view(ModelView(VTS))
admin.add_view(ModelView(WeatherCondition))
admin.add_view(ModelView(CoefficientDictionary))