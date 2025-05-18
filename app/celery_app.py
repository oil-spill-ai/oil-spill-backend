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

# Периодическая задача для очистки старых файлов (Celery Beat)
celery_app.conf.beat_schedule = {
    "cleanup-old-files": {
        "task": "tasks.cleanup_old_files",
        "schedule": 600.0,  # Каждые 10 минут
    },
}