from .celery_worker import celery_app
from .utils import send_to_ml_service, create_result_archive
import os

@celery_app.task(bind=True)
def process_archive_task(self, user_hash, file_paths):
    processed_files = []
    errors = []
    for file_path in file_paths:
        try:
            result_img_path = send_to_ml_service(file_path, user_hash)
            processed_files.append(result_img_path)
        except Exception as e:
            errors.append({"file": file_path, "error": str(e)})
    # Собрать архив с результатами
    archive_path = create_result_archive(user_hash)
    return {"archive": str(archive_path), "processed_files": processed_files, "errors": errors}
