# core/stream_manager.py

import logging
from infrastructure.redis_job_store import RedisJobStore

class QueueStreamManager:
    def __init__(self, queue, job_store: RedisJobStore):
        self.queue = queue
        self.job_store = job_store
        self.streams = queue.streams
        # Get last_ids of all priority streams
        self.last_ids = {stream: self.job_store.get_last_id(stream) for stream in self.streams} 

    def get_next_job(self):
        """
        Fetch next job from any available priority stream and tries streams in order of priority.
        Returns: (stream, msg_id, msg_data) or None
        """
        for stream in self.streams:
            try:
                result = self.job_store.read_from_stream(stream, self.last_ids[stream])
                if result:
                    msg_id, msg_data = result
                    return stream, msg_id, msg_data
            except Exception as e:
                logging.error(f"[stream] Error reading from stream {stream}: {e}")
                continue
        return None

    def mark_processed(self, stream: str, msg_id: str):
        """
        After successful or skipped processing, update the last_id.
        """
        self.last_ids[stream] = msg_id
        self.job_store.set_last_id(stream, msg_id)
