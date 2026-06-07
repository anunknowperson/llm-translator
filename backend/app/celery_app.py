from celery import Celery

from app.config import settings

# Асинхронная очередь задач: Celery + Redis как broker и result backend
celery_app = Celery(
    "translator",
    broker=settings.redis_broker_url,
    backend=settings.redis_backend_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    result_expires=60 * 60 * 24,
    task_track_started=True,
    worker_send_task_events=True,
)
