from .celery_worker import celery_app
import os
from pathlib import Path

def get_meta_path(archive_path: Path) -> Path:
    return archive_path.with_suffix(archive_path.suffix + '.meta')

@celery_app.task
def delete_file_task(archive_path_str: str):
    archive_path = Path(archive_path_str)
    user_dir = archive_path.parent
    try:
        # Удаляем всю папку пользователя и всё её содержимое
        if user_dir.exists() and user_dir.is_dir():
            for item in user_dir.iterdir():
                if item.is_file() or item.is_symlink():
                    try:
                        item.unlink()
                    except Exception as e:
                        print(f"[WARN] Не удалось удалить файл {item}: {e}")
                elif item.is_dir():
                    try:
                        import shutil
                        shutil.rmtree(item)
                    except Exception as e:
                        print(f"[WARN] Не удалось удалить подпапку {item}: {e}")
            try:
                user_dir.rmdir()
            except Exception as e:
                print(f"[WARN] Не удалось удалить папку пользователя {user_dir}: {e}")
    except Exception as e:
        print(f"[WARN] Не удалось полностью удалить папку пользователя {user_dir}: {e}")
