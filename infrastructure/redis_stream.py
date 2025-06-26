# infrastructure/redis_stream.py

import logging
from infrastructure.redis_queue import get_last_id, set_last_id

class QueueStreamManager:
    def __init__(self, queue):
        self.queue = queue
        self.client = queue.client
        self.streams = queue.streams
        self.last_ids = {stream: get_last_id(stream) for stream in self.streams} # Get last_ids of all priority streams

    def get_next_job(self):
        """
        Reads one job from the highest priority stream with available jobs.
        Returns: (stream, msg_id, msg_data) or None
        """
        for stream in self.streams:
            try:
                # Read from the current priority stream using XREAD.
                # # r.xread({stream: ID}) returns messages with IDs strictly greater than the given ID.
                # # This ensures the same message is not processed twice.
                res = self.client.xread({stream: self.last_ids[stream]}, block=1000, count=1)
                if not res:
                    continue
                _, messages = res[0]
                msg_id, msg_data = messages[0]
                return stream, msg_id, msg_data
            except Exception as e:
                logging.error(f"Stream read error on {stream}: {e}")
                continue
        return None

    def mark_processed(self, stream: str, msg_id: str):
        """
        After successful or skipped processing, update the last_id.
        """
        self.last_ids[stream] = msg_id
        set_last_id(stream, msg_id)
