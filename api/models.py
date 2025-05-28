# api/models.py

from pydantic_settings import BaseSettings
from typing import Dict
from pydantic import BaseModel

class JobRequest(BaseModel):
    payload: Dict

class JobResponse(BaseModel):
    job_id: str
    status: str
