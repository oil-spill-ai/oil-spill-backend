import os
import time
from datetime import datetime, timedelta
from app.celery_app import celery_app

RESULT_DIR = "results"
UPLOAD_DIR = "uploads"
EXPIRATION_HOURS = 1

@celery_app.task
def cleanup_old_files():
    now = time.time()
    cutoff = now - (EXPIRATION_HOURS * 60 * 60)

    for dir_path in [RESULT_DIR, UPLOAD_DIR]:
        if not os.path.exists(dir_path):
            continue
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            if os.path.isfile(file_path):
                created = os.path.getmtime(file_path)
                if created < cutoff:
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
