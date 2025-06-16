# api/routes/job_routes.py

from fastapi import APIRouter, HTTPException
from uuid import uuid4
from task_queues.redis_queue import (
    enqueue_job, get_job_status, cancel_job,
    STATUS_CANCELLED
)
from api.models import JobRequest, JobResponse

router = APIRouter()

@router.post("/", response_model=JobResponse)
def submit_job(job: JobRequest):
    job_id = str(uuid4())
    success = enqueue_job(job_id, job.payload, job.priority)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    return JobResponse(job_id=job_id, status="queued")

@router.get("/{job_id}", response_model=JobResponse)
def get_status(job_id: str):
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(job_id=job_id, status=status)

@router.post("/{job_id}/cancel")
def cancel_job_handler(job_id: str):
    current_status = get_job_status(job_id)

    if current_status is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if current_status in ["completed", "failed", "in_progress"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a job that is already completed, failed, or in progress."
            )

    if current_status == STATUS_CANCELLED:
        return {"job_id": job_id, "status": STATUS_CANCELLED, "message": "Job is already cancelled"}

    cancel_job(job_id)
    return {"job_id": job_id, "status": STATUS_CANCELLED}

