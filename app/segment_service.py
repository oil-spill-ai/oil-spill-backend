from fastapi import FastAPI

app = FastAPI()

@app.post("/segment")
async def segment_image():
    return {"mask": "base64_encoded_mask", "status": "success"}