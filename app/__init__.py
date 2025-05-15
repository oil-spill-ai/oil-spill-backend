from fastapi import FastAPI
from .tasks import process_images_task
from .services import upload_file, get_status

app = FastAPI()

@app.post("/upload")
async def upload_file_endpoint(file: UploadFile = File(...)):
    return await upload_file(file)

@app.get("/status/{job_id}")
async def get_status_endpoint(job_id: str):
    return await get_status(job_id)
