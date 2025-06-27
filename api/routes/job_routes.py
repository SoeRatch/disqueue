# api/routes/job_routes.py

from fastapi import APIRouter, HTTPException
from uuid import uuid4
from api.models import JobRequest, JobResponse


from config.status_codes import (
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
)

from infrastructure.redis_conn import redis_client
from infrastructure.redis_job_store import RedisJobStore
from config.queue_registry import REGISTERED_QUEUES
from core.queue_config import DisqueueQueue

router = APIRouter()

job_store = RedisJobStore(redis_client)

# Create a mapping of queue name to DisqueueQueue instance
registered_queues = {
    config.name: DisqueueQueue(config, redis_client)
    for config in REGISTERED_QUEUES
}

@router.post("/", response_model=JobResponse)
def submit_job(job: JobRequest):
    job_id = str(uuid4())

    queue_name = job.queue_name or "default"
    queue = registered_queues.get(queue_name)

    if not queue:
        raise HTTPException(status_code=400, detail=f"Queue '{queue_name}' not registered.")
    
    try:
        success = queue.enqueue(job_id, job.payload, job.priority.lower())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    
    return JobResponse(job_id=job_id, status="queued")


@router.get("/{job_id}", response_model=JobResponse)
def get_status(job_id: str):
    status = job_store.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(job_id=job_id, status=status)


@router.post("/{job_id}/cancel")
def cancel_job_handler(job_id: str):
    current_status = job_store.get_job_status(job_id)

    if current_status is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if current_status in {STATUS_COMPLETED, STATUS_FAILED, STATUS_IN_PROGRESS}:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a job that is already completed, failed, or in progress."
            )

    if current_status == STATUS_CANCELLED:
        return {"job_id": job_id, "status": STATUS_CANCELLED, "message": "Job is already cancelled"}

    job_store.cancel_job(job_id)
    return {"job_id": job_id, "status": STATUS_CANCELLED}

