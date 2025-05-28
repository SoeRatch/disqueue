# api/routes.py

from fastapi import APIRouter, HTTPException
from uuid import uuid4
from queue.redis_queue import enqueue_job, get_job_status
from api.models import JobRequest, JobResponse

router = APIRouter()

@router.post("/", response_model=JobResponse)
def submit_job(job: JobRequest):
    job_id = str(uuid4())
    success = enqueue_job(job_id, job.payload)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to enqueue job")
    return JobResponse(job_id=job_id, status="queued")

@router.get("/{job_id}", response_model=JobResponse)
def get_status(job_id: str):
    status = get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(job_id=job_id, status=status)
