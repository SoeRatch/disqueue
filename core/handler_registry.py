# core/handler_registry.py

from typing import Callable, Dict, Optional

_handler_map: Dict[str, Callable] = {}

def register_handler(queue_name: str, handler: Callable):
    """
    Register a handler function for a specific queue name.
    """
    _handler_map[queue_name] = handler

def get_handler(queue_name: str) -> Optional[Callable]:
    """
    Retrieve the handler function for a given queue name.
    """
    return _handler_map.get(queue_name)

def list_registered_handlers() -> Dict[str, str]:
    """
    Debug utility to list registered handlers.
    """
    return {queue: func.__name__ for queue, func in _handler_map.items()}
