Чтобы запустить проект нужно прописать две команды в разных башах
1) celery -A app.celery_app worker --loglevel=info
2) uvicorn app.main:app --reload --port 8000