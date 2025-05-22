from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from utils import extract_archive, create_archive
from tasks import process_image
from celery.result import AsyncResult
import os
import uuid
import shutil

router = APIRouter()

UPLOAD_DIR = "uploads"
RESULT_DIR = "results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)


@router.post("/upload/")
async def upload_archive(request: Request, file: UploadFile = File(...)):

    # Проверка на тип запроса (Content-Type)
    content_type = request.headers.get("Content-Type", "")
    if "multipart/form-data" not in content_type:
        raise HTTPException(
            status_code=415,
            detail="Content-Type must be multipart/form-data. Use a form or file upload tool."
        )

    # Проверка имени файла
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Only .zip files are supported."
        )

    # Проверка MIME-типа
    if file.content_type not in ["application/zip", "application/x-zip-compressed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Expected a zip archive."
        )

    # Генерация job_id и путей
    job_id = str(uuid.uuid4())
    archive_path = os.path.join(UPLOAD_DIR, f"{job_id}")

    # Сохраняем исходный архив
    with open(archive_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Распаковка исходного архива
    extract_dir = archive_path + "_extracted"
    extract_archive(archive_path, extract_dir)

    # Постановка задач в Celery
    task_ids = []
    for filename in os.listdir(extract_dir):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            file_path = os.path.join(extract_dir, filename)
            task = process_image.delay(job_id, file_path)
            task_ids.append(task.id)

    return {
        "job_id": job_id,
        "task_ids": task_ids,
        "status": "processing_started"
    }


@router.get("/download/{filename}")
def download_result(filename: str):
    file_path = os.path.join(RESULT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=410,  # 410 Gone - ресурс больше недоступен
            detail="Архив с результатами был автоматически удален. Пожалуйста, загрузите файлы заново."
        )
    return FileResponse(file_path, filename=filename)


@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    task = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }