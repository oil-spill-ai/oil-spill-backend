from .celery_worker import celery_app
import os
from pathlib import Path

def get_meta_path(archive_path: Path) -> Path:
    return archive_path.with_suffix(archive_path.suffix + '.meta')

@celery_app.task
def delete_file_task(archive_path_str: str):
    archive_path = Path(archive_path_str)
    meta_path = get_meta_path(archive_path)
    try:
        if archive_path.exists():
            os.remove(archive_path)
        if meta_path.exists():
            os.remove(meta_path)
        # Удаляем папку пользователя, если она пуста
        user_dir = archive_path.parent
        try:
            user_dir.rmdir()  # удаляет только если папка пуста
        except OSError:
            # Папка не пуста — ничего не делаем
            pass
    except Exception as e:
        print(f"[WARN] Не удалось удалить архив, мета-файл или папку {archive_path}: {e}")
