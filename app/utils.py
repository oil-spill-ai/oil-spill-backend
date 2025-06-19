import os
import zipfile
import hashlib
import uuid
from pathlib import Path
import aiofiles
import shutil
import requests

ARCHIVE_LIFETIME_SECONDS = 600  # Синхронизировано с main.py

def make_user_hash():
    # Можно заменить на более сложный, если нужно
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]

def get_user_dir(user_hash: str) -> Path:
    base = Path("results") / user_hash
    base.mkdir(parents=True, exist_ok=True)
    return base

async def save_and_extract_archive(upload_file, user_dir: Path, user_hash: str):
    archive_path = user_dir / f"input_{user_hash}.zip"
    async with aiofiles.open(archive_path, 'wb') as out_file:
        content = await upload_file.read()
        await out_file.write(content)

    extracted_files = []
    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            # Пропустить директории и служебные файлы
            if member.endswith('/') or '__MACOSX' in member or member.startswith('.'):
                continue
            filename = os.path.basename(member)
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']:
                # Переименование файла с добавлением user_hash в имя
                new_filename = f"{os.path.splitext(filename)[0]}_{user_hash}{ext}"
                out_path = user_dir / new_filename
                with zip_ref.open(member) as source, open(out_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
                extracted_files.append(out_path)
    # Удаляем архив после разархивирования
    try:
        os.remove(archive_path)
    except Exception as e:
        print(f"[WARN] Не удалось удалить архив {archive_path}: {e}")
    return extracted_files

def send_to_ml_service(file_path: str, user_hash: str) -> str:
    ml_url = os.getenv("ML_SERVICE_URL", "http://localhost:8002/segment")
    with open(file_path, "rb") as f:
        files = {'file': (os.path.basename(file_path), f, 'image/jpeg')}
        response = requests.post(ml_url, files=files)

    if response.status_code == 200:
        result_dir = get_user_dir(user_hash)
        result_path = result_dir / f"result_{os.path.basename(file_path)}"
        # Проверка Content-Type и размера
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/') or not response.content or len(response.content) < 100:
            # Не сохраняем невалидный файл
            raise Exception(f"ML service returned invalid image: content-type={content_type}, size={len(response.content)}")
        with open(result_path, "wb") as out:
            out.write(response.content)
        # Удаляем исходный файл после отправки и получения результата
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"[WARN] Не удалось удалить файл {file_path}: {e}")
        return str(result_path)
    else:
        raise Exception(f"ML service error: {response.status_code}, {response.text}")

def create_result_archive(user_hash: str) -> Path:
    from .delete_tasks import delete_file_task, get_meta_path
    import time
    user_dir = get_user_dir(user_hash)
    result_files = []
    archive_name = f"result_{user_hash}.zip"
    for file in user_dir.iterdir():
        if file.name.startswith("result_") and file.name != archive_name and not file.name.endswith(".meta"):
            new_name = file.name.replace("result_", "").replace(f"_{user_hash}", "")
            result_files.append((file, new_name))
    result_archive = user_dir / archive_name
    with zipfile.ZipFile(result_archive, 'w') as zipf:
        for file, new_name in result_files:
            zipf.write(file, arcname=new_name)
    # Сохраняем время создания архива в meta-файл
    meta_path = get_meta_path(result_archive)
    with open(meta_path, 'w') as f:
        f.write(str(int(time.time())))
    # Ставим задачу на удаление архива через 10 минут
    delete_file_task.apply_async(args=[str(result_archive)], countdown=ARCHIVE_LIFETIME_SECONDS)
    return result_archive
