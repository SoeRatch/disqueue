# worker/worker.py

import json
import time
from queue.redis_queue import r, JOB_STREAM, mark_job_status

def process(payload: dict):
    print("Processing:", payload)
    time.sleep(2)

def start_worker():
    print("Worker started...")
    while True:
        try:
            # Continuously listens to Redis Stream (XREAD) for new jobs.
            res = r.xread({JOB_STREAM: "$"}, block=5000, count=1)
            if not res:
                continue

            _, messages = res[0]
            for msg_id, msg_data in messages:
                job_id = msg_data.get("job_id")
                payload = json.loads(msg_data.get("payload", "{}"))

                print(f"Got job {job_id}")
                mark_job_status(job_id, "in_progress")
                try:
                    process(payload)
                    mark_job_status(job_id, "completed")
                except Exception as e:
                    print(f"Job {job_id} failed: {e}")
                    mark_job_status(job_id, "failed")

        except Exception as e:
            print("Worker error:", e)
            time.sleep(1)

if __name__ == "__main__":
    start_worker()
