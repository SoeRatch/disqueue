# api/routes/queue_routes.py

from fastapi import APIRouter
from core.registry import get_registered_queues

router = APIRouter()

@router.get("/", summary="List registered queues")
def list_queues():
    queues = get_registered_queues()
    return [
        {
            "name": q.name,
            "priorities": q.config.priorities,
            "enable_dlq": q.config.enable_dlq,
            "retry_limit": q.config.retry_limit
        }
        for q in queues
    ]
