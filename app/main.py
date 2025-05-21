from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os


from api import router

app = FastAPI(
    title="Oil Spill Detection Backend",
    max_upload_size=100_000_000  # 100MB
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключение API маршрутов
app.include_router(router, prefix="/api")

# Статические файлы (frontend)
from fastapi.responses import FileResponse
from starlette.requests import Request
from starlette.responses import Response

frontend_dir = os.path.join(os.path.dirname(__file__), "frontend", "out")  # путь до сборки фронта
if os.path.exists(frontend_dir):
    class SPAStaticFiles(StaticFiles):
        async def get_response(self, path, scope):
            try:
                response = await super().get_response(path, scope)
                if response.status_code == 404:
                    # Если не найдено — отдаём index.html (SPA fallback)
                    return await super().get_response("index.html", scope)
                return response
            except Exception:
                return await super().get_response("index.html", scope)
    app.mount("/", SPAStaticFiles(directory=frontend_dir, html=True), name="frontend")