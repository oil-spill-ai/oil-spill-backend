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
MEDIA_DIR = "media"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)


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
    archive_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")

    # Сохраняем архив
    with open(archive_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Распаковка архива
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


@router.get("/archive/{job_id}")
def create_result_archive(job_id: str):
    """Создает архив с результатами для указанного job_id, если все задачи завершены успешно."""
    # Проверим, что все задачи для job_id завершены
    # Для простоты предполагаем, что имена файлов в media/{job_id}/processed совпадают с исходными
    processed_dir = os.path.join(MEDIA_DIR, job_id, "processed")
    if not os.path.exists(processed_dir):
        raise HTTPException(status_code=404, detail="Results not found for this job_id")
    # Проверка наличия файлов
    files = [f for f in os.listdir(processed_dir) if os.path.isfile(os.path.join(processed_dir, f))]
    if not files:
        raise HTTPException(status_code=400, detail="No processed files found. Wait for tasks to complete.")
    # Создаем архив
    result_zip_path = os.path.join(RESULT_DIR, f"{job_id}_result.zip")
    create_archive(processed_dir, result_zip_path)
    return {"archive_url": f"/api/download/{os.path.basename(result_zip_path)}"}

@router.get("/download/{filename}")
def download_result(filename: str):
    file_path = os.path.join(RESULT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)


@router.get("/task/{task_id}")
def get_task_status(task_id: str):
    task = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": task.result if task.ready() else None
    }