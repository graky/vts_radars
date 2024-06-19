from celery import Celery


celery_app = Celery(
    "celery_queue",
    broker="amqp://guest:guest@localhost:5672/",
    include=["celery_queue.tasks"]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
celery_app.conf.beat_schedule = {
    "update_ship_positions": {
        "task": "celery_queue.tasks.update_ship_positions",
                'schedule': 5.0,
    },
}
