# handlers/registry.py

from core.handler_registry import register_handler
import time
import logging

def handle_default_job(payload):
    logging.info(f"[Handler:default] Processing: {payload}")
    time.sleep(30)

def handle_image_job(payload):
    logging.info(f"[Handler:image_processing] Handling image task: {payload}")
    time.sleep(30)

register_handler("default", handle_default_job)
register_handler("image_processing", handle_image_job)
