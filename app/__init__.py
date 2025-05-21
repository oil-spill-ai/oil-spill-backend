from .celery_worker import celery_app  # Экспортируем celery_app для Celery autodiscover
from . import delete_tasks, tasks  # Импортируем задачи, чтобы они регистрировались
