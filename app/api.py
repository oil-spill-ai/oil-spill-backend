from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
from utils import extract_archive, create_archive, get_preview_images
from ml_client import run_mock_model
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

    # Сохраняем архив
    archive_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(archive_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Распаковка архива
    extract_dir = archive_path + "_extracted"
    extract_archive(archive_path, extract_dir)

    # Заглушка — ML-модель
    run_mock_model(extract_dir)

    # Архивируем результат
    result_zip_path = os.path.join(RESULT_DIR, f"{uuid.uuid4()}_result.zip")
    create_archive(extract_dir, result_zip_path)

    # Генерация предпросмотра
    preview_images = get_preview_images(extract_dir)

    return {
        "archive_url": f"/download/{os.path.basename(result_zip_path)}",
        "preview_images": preview_images,
    }


@router.get("/download/{filename}")
def download_result(filename: str):
    file_path = os.path.join(RESULT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)
