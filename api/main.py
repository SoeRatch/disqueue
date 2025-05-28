# api/main.py

from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="DisQueue: Distributed Job Queue System")

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(router, prefix="/jobs")
