from celery import Celery
import os

# Настройки Celery
celery_app = Celery(
    "oil_spill_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["tasks"]
)

# Конфигурация
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
