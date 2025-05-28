# api/models.py

from pydantic import BaseModel

class JobRequest(BaseModel):
    payload: dict

class JobResponse(BaseModel):
    job_id: str
    status: str
