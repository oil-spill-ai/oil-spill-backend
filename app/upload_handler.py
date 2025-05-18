import hashlib
import os
import uuid
from typing import Optional

def generate_job_id(user_id: str, filename: str) -> str:
    """Генерирует уникальный job_id."""
    unique_str = f"{user_id}_{filename}_{uuid.uuid4()}"
    return hashlib.sha256(unique_str.encode()).hexdigest()

def prepare_upload(user_id: str, file_path: str) -> str:
    """Подготавливает директории и возвращает job_id."""
    job_id = generate_job_id(user_id, os.path.basename(file_path))
    tmp_dir = os.path.join("/tmp", job_id)
    os.makedirs(tmp_dir, exist_ok=True)
    return job_id