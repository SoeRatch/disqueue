# api/models.py

from pydantic_settings import BaseSettings
from typing import Dict, Literal
from pydantic import BaseModel
from config.settings import settings

class JobRequest(BaseModel):
    payload: Dict
    priority: Literal['high', 'medium', 'low'] = settings.default_priority

class JobResponse(BaseModel):
    job_id: str
    status: str
