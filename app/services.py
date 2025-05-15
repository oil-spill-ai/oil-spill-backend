# Содержит логику для обработки загрузки файлов,
# взаимодействия с YOLO, отправки изображений на микросервис
# и получения статуса задач

import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile, File
from .tasks import process_images_task
import requests

UPLOAD_DIR = Path("/tmp/uploads")
RESULT_DIR = Path("/tmp/results")

async def upload_file(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    job_id = str(uuid.uuid4())
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(file_path), str(job_dir))
    task = process_images_task.apply_async(args=[job_id])
    return {"task_id": task.id}

def process_image_with_yolo(image_path: Path):
    url = "http://yolo_microservice_url/process_image"
    with open(image_path, "rb") as image_file:
        response = requests.post(url, files={"image": image_file})
    if response.status_code == 200:
        result_path = RESULT_DIR / image_path.name
        with open(result_path, "wb") as f:
            f.write(response.content)

async def get_status(job_id: str):
    status = r.get(job_id)
    if status is None:
        return {"status": "Task not found"}
    return {"status": status.decode("utf-8")}
