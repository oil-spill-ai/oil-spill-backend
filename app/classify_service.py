from fastapi import FastAPI

app = FastAPI()

@app.post("/classify")
async def classify_image():
    return {"class": "oil_spill", "confidence": 0.95}