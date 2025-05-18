# задача Celery, которая управляет процессом обработки изображений

from celery import Celery
from .services import process_image_with_yolo

celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@celery_app.task
def process_images_task(job_id: str):
    try:
        job_dir = Path("/tmp/uploads") / job_id
        images = list(job_dir.glob("*.jpg"))
        for image in images:
            process_image_with_yolo(image)
        r.set(job_id, "Processed")
    except Exception as e:
        r.set(job_id, f"Error: {str(e)}")
