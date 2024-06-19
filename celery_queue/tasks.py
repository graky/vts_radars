from structures import Ship
from celery.utils.log import get_task_logger
from celery import shared_task

logger = get_task_logger(__name__)

@shared_task
def update_ship_positions():
    print("here task")
    print("updating ship positions...")
    logger.info("Updating ship positions...")
    ships = Ship.load_from_db()
    for ship in ships:
        ship.update_position()
