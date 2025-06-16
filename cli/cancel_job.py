# cli/cancel_job.py

import sys
from task_queues.redis_queue import cancel_job

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cancel_job.py <job_id>")
        sys.exit(1)

    job_id = sys.argv[1]
    success = cancel_job(job_id)
    print(f"Cancelled: {success}")
