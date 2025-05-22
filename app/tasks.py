from celery_app import celery_app
import os
import shutil
import requests
import glob
from pathlib import Path
from utils import create_archive

ML_SERVICE_URL = "http://localhost:8002"  # URL ML-сервиса
UPLOAD_DIR = "uploads"
RESULT_DIR = "results"

@celery_app.task(name="process_image")
def process_image(job_id: str, file_path: str):
    """Обрабатывает изображение в ML-сервис и сохраняет результат."""
    output_dir = Path(RESULT_DIR) / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Определяем mime-type по расширению файла
        ext = Path(file_path).suffix.lower()
        if ext in [".jpg", ".jpeg"]:
            mime = "image/jpeg"
        elif ext == ".png":
            mime = "image/png"
        else:
            mime = "application/octet-stream"
        # Отправка файла в ML-сервис
        with open(file_path, 'rb') as f:
            try:
                response = requests.post(
                    f"{ML_SERVICE_URL}/segment",
                    files={'file': (Path(file_path).name, f, mime)},
                    timeout=30
                )
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"Failed to connect to ML service: {str(e)}"
                }
        if response.status_code == 200:
            # Сохраняем результат
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                output_path = output_dir / Path(file_path).name
                with open(output_path, 'wb') as out_file:
                    out_file.write(response.content)

                # Создаем архив с результатами
                processed_dir = os.path.join(RESULT_DIR, job_id)
                result_zip_path = os.path.join(RESULT_DIR, f"{job_id}_result.zip")
                create_archive(processed_dir, result_zip_path)

                # Удаляем исходный архив
                original_archive = os.path.join(UPLOAD_DIR, f"{job_id}_*.zip")
                for archive in glob.glob(original_archive):
                    os.remove(archive)

                # Запускаем задачу на удаление исходных файлов через 30 секунд
                cleanup_original_files.apply_async((job_id,), countdown=30)

                # Запускаем задачу на удаление результатов через 10 минут
                cleanup_job_files.apply_async((job_id,), countdown=600)

                return {
                    "status": "success",
                    "job_id": job_id,
                    "processed_path": str(output_path)
                }
            else:
                return {
                    "status": "error",
                    "error": "ML service did not return an image",
                    "details": response.text
                }
        else:
            return {
                "status": "error",
                "error": f"ML service error: {response.status_code}",
                "details": response.text
            }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(name="cleanup_original_files")
def cleanup_original_files(job_id: str):
    """Удаляет исходные файлы конкретного job_id через 30 секунд после создания итогового архива."""

    # Ищем папки, которые начинаются с job_id и заканчиваются на .zip_extracted
    matching_dirs = glob.glob(os.path.join(UPLOAD_DIR, f"{job_id}*.zip_extracted"))

    # Удаляем все найденные папки (если их несколько)
    for dir_path in matching_dirs:
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path)


@celery_app.task(name="cleanup_job_files")
def cleanup_job_files(job_id: str):
    """Удаляет файлы конкретного job_id через 10 минут после создания итогового архива."""
    processed_dir = os.path.join(RESULT_DIR, job_id)
    result_zip_path = os.path.join(RESULT_DIR, f"{job_id}_result.zip")

    if os.path.exists(processed_dir):
        shutil.rmtree(processed_dir)
    if os.path.exists(result_zip_path):
        os.remove(result_zip_path)
