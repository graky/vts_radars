# api.py
from fastapi import FastAPI

from structures import Ship
from db import  admin

app = FastAPI()
admin.mount_to(app)


@app.get("/ships")
def get_ships(reload: bool = False, update: bool = False):
    ships = Ship.load_from_db()
    if reload:  # если был запрос на обновление, задаем новые стартовые позиции
        for ship in ships:
            ship.start_positions()  # задаем случайные стартовые координаты
    return [ship.to_dict() for ship in ships]

# ships = [
#     Ship(name='Ship1', nationality='CountryA', length=200, width=30, bearing=90, speed=20),
#     Ship(name='Ship2', nationality='CountryB', length=150, width=25, bearing=180, speed=15)
# ]
