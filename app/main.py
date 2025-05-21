import os
import shutil
import zipfile
import hashlib
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from .tasks import process_archive_task
from .utils import save_and_extract_archive, make_user_hash, create_result_archive, get_user_dir
from .delete_tasks import get_meta_path
import time

ARCHIVE_LIFETIME_SECONDS = 600  # Синхронизировано с utils.py

app = FastAPI()

# CORS (настройте под свой фронт)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

@app.post("/api/upload")
async def upload_archive(file: UploadFile = File(...)):
    # Сохраняем архив и извлекаем
    user_hash = make_user_hash()
    user_dir = get_user_dir(user_hash)
    user_dir.mkdir(parents=True, exist_ok=True)
    extracted_files = await save_and_extract_archive(file, user_dir, user_hash)
    if not extracted_files:
        raise HTTPException(status_code=400, detail="No files extracted from archive")

    # Запускаем celery задачу для обработки файлов
    task = process_archive_task.delay(user_hash, [str(f) for f in extracted_files])
    return {"status": "processing", "job_id": task.id, "user_hash": user_hash}

@app.get("/api/download/{user_hash}")
def download_result(user_hash: str):
    archive_path = create_result_archive(user_hash)
    if not archive_path or not archive_path.exists():
        raise HTTPException(status_code=404, detail="Result archive not found")
    return FileResponse(archive_path, media_type="application/zip", filename=f"result_{user_hash}.zip")

@app.get("/api/status/{job_id}")
def get_status(job_id: str):
    from celery.result import AsyncResult
    from .celery_worker import celery_app
    result = AsyncResult(job_id, app=celery_app)
    return {"status": result.status, "result": result.result}

@app.get("/api/archive_time_left/{user_hash}")
def archive_time_left(user_hash: str):
    user_dir = get_user_dir(user_hash)
    archive_path = user_dir / f"result_{user_hash}.zip"
    meta_path = get_meta_path(archive_path)
    if not archive_path.exists() or not meta_path.exists():
        return {"seconds_left": 0}
    try:
        with open(meta_path, 'r') as f:
            created_at = int(f.read().strip())
    except Exception:
        return {"seconds_left": 0}
    now = int(time.time())
    seconds_left = ARCHIVE_LIFETIME_SECONDS - (now - created_at)
    if seconds_left < 0:
        seconds_left = 0
    return {"seconds_left": seconds_left}
