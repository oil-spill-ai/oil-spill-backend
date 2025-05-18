from celery_app import celery_app
import os
import shutil
import time
from datetime import datetime, timedelta

UPLOAD_DIR = "uploads"
RESULT_DIR = "results"
MEDIA_DIR = "media"

@celery_app.task(name="process_image")
def process_image(job_id: str, file_path: str):
    """Обрабатывает изображение и сохраняет результат."""
    output_dir = os.path.join(MEDIA_DIR, job_id)
    os.makedirs(output_dir, exist_ok=True)

    # Заглушка обработки (замените на реальную ML-логику)
    # Пример: копируем файл в папку результата
    shutil.copy(file_path, output_dir)

    return {"status": "success", "job_id": job_id}

@celery_app.task(name="cleanup_old_files")
def cleanup_old_files():
    """Удаляет файлы старше 24 часов."""
    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    for root, dirs, files in os.walk(MEDIA_DIR):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            mod_time = datetime.fromtimestamp(os.path.getmtime(dir_path))
            if mod_time < cutoff:
                shutil.rmtree(dir_path)