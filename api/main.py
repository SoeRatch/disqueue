# api/main.py

from fastapi import FastAPI
from api.routes import job_routes, queue_routes

app = FastAPI(title="DisQueue: Distributed Job Queue System")

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(job_routes.router, prefix="/jobs", tags=["Jobs"])
app.include_router(queue_routes.router, prefix="/queues", tags=["Queues"])
