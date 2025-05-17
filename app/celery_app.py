from celery import Celery

# Настройка Celery для подключения к Redis
celery_app = Celery(
    "oil_spill_app",
    broker="redis://localhost:6379/0",  # Подключение к Redis
    backend="redis://localhost:6379/0"  # Используем Redis для хранения результатов
)

celery_app.conf.timezone = 'UTC'
celery_app.conf.accept_content = ['json']
celery_app.conf.task_serializer = 'json'
