# api/models.py

from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field
from config.settings import settings

class JobRequest(BaseModel):
    queue_name: Optional[str] = Field(default="default", description="Target queue name")
    priority: Optional[Literal["high", "medium", "low", "default"]] = Field(
        default=settings.default_priority, description="Job priority"
    )
    payload: Dict

class JobResponse(BaseModel):
    job_id: str
    status: str
