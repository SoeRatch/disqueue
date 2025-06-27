# infrastructure/redis_stream.py

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
                # Read from the current priority stream using XREAD.
                # # xread({stream: ID}) returns messages with IDs strictly greater than the given ID.
                # # This ensures the same message is not processed twice.
                res = self.job_store.client.xread({stream: self.last_ids[stream]}, block=1000, count=1)
                if not res:
                    continue
                _, messages = res[0]
                msg_id, msg_data = messages[0]
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
