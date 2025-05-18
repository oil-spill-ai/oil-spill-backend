from celery_app import celery_app
import os
import shutil
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

ML_SERVICE_URL = "http://localhost:8002"  # URL ML-сервиса
UPLOAD_DIR = "uploads"
RESULT_DIR = "results"
MEDIA_DIR = "media"

@celery_app.task(name="process_image")
def process_image(job_id: str, file_path: str):
    """Обрабатывает изображение в ML-сервис и сохраняет результат."""
    output_dir = Path(MEDIA_DIR) / job_id / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Отправка файла в ML-сервис
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{ML_SERVICE_URL}/segment",
                files={'file': (Path(file_path).name, f, 'image/jpeg')},
                timeout=30
            )

        if response.status_code == 200:
            # Сохранение результата
            output_path = output_dir / Path(file_path).name
            with open(output_path, 'wb') as out_file:
                out_file.write(response.content)

            return {
                "status": "success",
                "job_id": job_id,
                "processed_path": output_path
            }

        return {
            "status": "error",
            "error": f"ML service returned {response.status_code}",
            "details": response.text
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@celery_app.task(name="cleanup_old_files")
def cleanup_old_files():
    """Удаляет файлы старше 24 часов."""
    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    for root, dirs, files in os.walk(MEDIA_DIR):
        for name in dirs + files:
            path = Path(root) / name
            if path.stat().st_mtime < cutoff.timestamp():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()