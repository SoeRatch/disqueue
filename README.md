# Disqueue

**Disqueue** is a minimal, lightweight distributed job queue system inspired by Celery and BullMQ. Built with FastAPI, Redis Streams, and Docker, it supports job prioritization, retries, cancellation, dead-letter queue and Redis-powered idempotency and deduplication — all while staying simple and easy to reason about.

---
## Table of Contents

- [Features](#features)  
- [Stack](#stack)
- [Architecture Overview](#architecture-overview)
- [Components](#components) 
- [Directory Structure](#directory-structure)  
- [Getting Started](#getting-started)  
  - [Prerequisites](#prerequisites)  
  - [Setup Instructions](#setup-instructions)  
- [Usage](#example-usage)  
  - [Queue a Job](#1-queue-a-job)  
  - [Check Job Status](#2-check-job-status)  
  - [Simulate a Failing Job](#3-simulate-a-failing-job)  
- [Retry Mechanism](#retry-mechanism)  
- [Dead-letter Queue (DLQ)](#dead-letter-queue-dlq)
- [Idempotency & Deduplication](#idempotency--deduplication)
- [Configuration](#configuration)  
- [What’s Next](#whats-next) 
- [Technologies Used](#technologies-used)  
- [Author](#author)  
- [License](#license)

---

## Features

- **Job Submission**: Submit jobs via a REST API to queue jobs.
- **Status Tracking**: Monitor job states like `queued`, `in_progress`, `retrying`, `completed`,`failed` and `cancelled`.
- **Redis Integration**: Uses Redis Streams and Hashes for job management.
- **Retry Mechanism**: Automatic retries for failed jobs up to a configurable maximum.
- **Dockerized**: Easily reproducible local development environment.
- **Priority Handling**: Supports `high`, `medium`, and `low` priority job queues.
- **Dead-letter Queue (DLQ)**: Automatically moves jobs to a DLQ after exceeding retry limit for later inspection or manual retry.
- **Job Cancellation**: Cancel jobs before they are processed by a worker.
- **Idempotency & Deduplication**: Redis-powered lock mechanism ensures a job is never processed by more than one worker simultaneously.


---

## Stack

- **FastAPI** – REST API server
- **Redis Streams** – Priority queues
- **Python** – Worker logic and APIs
- **Docker & Docker Compose** – Containerization

---

## Architecture Overview

- Jobs are added to Redis Streams based on their priority level.
- Job metadata like status, retry count, and last stream ID is stored in Redis Hashes.
- Worker continuously reads from streams in strict priority order.
- Deduplication logic ensures only one worker processes a job at a time.
- Failed jobs are retried up to a max retry limit and then moved to a Dead-letter Queue (DLQ).
- FastAPI provides endpoints to submit and query jobs.
- Cancelled jobs are marked with cancelled status and skipped by workers, while maintaining stream offsets to avoid reprocessing.
- The worker is composed of a StreamManager for handling Redis stream offsets and polling, and a JobProcessor for managing job execution, retries, deduplication, and DLQ handling.

---

## Components

### `api/` – FastAPI Service
- POST `/jobs/` – Submit a job with payload and priority.
- GET `/jobs/{job_id}` – Retrieve the status of a specific job.
- POST `/jobs/{job_id}/cancel` – Cancel a job if it's still queued or retrying.

### `worker/worker.py` – Worker Orchestrator
- Continuously polls Redis Streams (`XREAD`) in strict priority order.
- Delegates job execution to `JobProcessor`.
- Uses `StreamManager` to manage stream offsets and fetch jobs.
- Skips cancelled jobs and advances the stream pointer to avoid reprocessing.

### `streams/manager.py` – Stream Manager
- Manages stream offsets (`last_id`) for each priority stream.
- Handles reading jobs using `XREAD` from Redis.
- Ensures each message is read and acknowledged only once.
- Cleanly decouples stream reading from job processing.

### `jobs/processor.py` – Job Processor
- Executes jobs with:
  - Redis-based deduplication lock.
  - Retry strategy (fixed or exponential).
  - Status tracking (`in_progress`, `completed`, etc.).
  - DLQ handoff after exhausting retries.
- Isolates the business logic from stream reading and orchestration.

### `utils/deduplication.py`
- Provides a reusable `@deduplicated()` decorator that wraps job processing in a Redis `SET NX` lock.
- Ensures only the first worker to acquire the lock executes the job.
- Automatically releases the lock on failure or marks it `done` on success.

### `task_queues/redis_queue.py`
- Redis utility functions for:
  - Enqueueing
  - Tracking job status and retries
  - Managing stream offsets
  - Sending failed jobs to DLQ

---

## Directory Structure

```
disqueue/
├── api/
│   ├── main.py          # FastAPI application
│   └── models.py        # Pydantic models for request/response
├── config/
│   └── settings.py      # Configuration settings
├── task_queues/
│   └── redis_queue.py   # Redis interaction logic
├── utils/
│   └── deduplication.py # Idempotency and deduplication logic
├── worker/
│   └── worker.py        # Worker process to handle jobs
├── streams/
│   └── manager.py        # Stream reading and offset tracking
├── jobs/
│   └── processor.py      # Core job execution logic
├── Dockerfile.api       # Dockerfile for API service
├── Dockerfile.worker    # Dockerfile for Worker service
├── docker-compose.yml   # Docker Compose configuration
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Setup Instructions

1. **Clone the Repository**:

    ```bash
    git clone https://github.com/SoeRatch/disqueue.git
    cd disqueue
    ```

2. **Create the `.env` File**:

   Copy the provided `.env.example` file and update it with your local environment credentials:

   ```bash
   cp .env.example .env
   ```

   > **Note**: Never commit the `.env` file to version control. It should be ignored in `.gitignore`.


3. **Start Docker Services**:

    On first run or after making changes to dependencies:
    ```bash
    docker compose up --build -d
    ```

    On subsequent runs:
    ```bash
    docker compose up -d
    ```

    Services started:

    - `api` at [http://localhost:8000](http://localhost:8000)
    - `worker` (background processor)
    - `redis` (stream/message broker)

---

## Example Usage

### 1. Queue a Job:

 POST `/jobs/` to submit a job with payload and priority.

  ```bash
  curl -X POST http://localhost:8000/jobs/ \
      -H "Content-Type: application/json" \
      -d '{"payload": {"msg": "urgent"}, "priority": "high"}'
  ```
  ```bash
  curl -X POST http://localhost:8000/jobs/ \
      -H "Content-Type: application/json" \
      -d '{"payload": {"msg": "medium"}, "priority": "low"}'
  ```

 Response:

  ```json
  {
    "job_id": "uuid-1234",
    "status": "queued"
  }
  ```

### 2. Check Job Status:

```bash
curl http://localhost:8000/jobs/uuid-1234
```

Response:

```json
{
  "job_id": "uuid-1234",
  "status": "completed"
}
```

### 3. Simulate a Failing Job:

```bash

curl -X POST http://localhost:8000/jobs/ \
     -H "Content-Type: application/json" \
     -d '{"payload": {"fail": true}, "priority": "medium"}'
```

The system will retry the job up to the `MAX_RETRIES` limit.

### 4. Cancel a Queued Job:
Cancels a job that is either queued or retrying.
```bash
curl -X POST http://localhost:8000/jobs/uuid-1234/cancel
```
Response:

```json
{
  "job_id": "uuid-1234",
  "status": "cancelled"
}
```
> **Note:** If the job is already in progress or completed, cancellation will not stop it.

---

## Retry Mechanism

- If a job fails (e.g., the payload contains `"fail": true`), the system retries it.
- Retries are capped at a configurable `max_retries` (default: 3).
- Two retry strategies are supported:
  - **fixed**: Retry after a constant delay (e.g., 1 second).
  - **exponential**: Retry after increasing delays (e.g., 1s → 2s → 4s → 8s).
- The strategy and delays are configured in the `.env` file.
- Once retries are exhausted, the job is moved to the **Dead-letter Queue**.

---



## Dead-letter Queue (DLQ)

Jobs that exceed the maximum retry limit are moved to a Redis Stream called `job:dlq` for post-mortem analysis.

Each DLQ message includes:
- `job_id`: Original job ID
- `payload`: Original job payload
- `reason`: Reason for failure (e.g., exception message)

You can inspect the DLQ via Redis CLI:

```bash
# In Redis CLI (local)
127.0.0.1:6379> XRANGE job:dlq - +
```
---

## Idempotency & Deduplication

In distributed queue systems, it’s common for the same job to be picked up more than once — either due to retries, network glitches, or multiple workers competing. Disqueue avoids this using a Redis-based locking mechanism via a reusable decorator.

The core logic is defined in `utils/deduplication.py` and applied to the job processor in `worker/worker.py`:

```python
# worker/worker.py

@deduplicated()
def safe_process(job_id, payload):
    logging.info(f"Processing job {job_id}")
    time.sleep(10)  # Simulated long task
    if payload.get("fail"):
        raise Exception("Simulated failure")
```

### How it works
- When a job is picked up, a Redis key `dedup:{job_id}` is set using `SET NX`, acting as a lock.
- If the key already exists, the job is considered already in progress or processed — so it’s skipped.
- On successful execution, the lock is converted to a `done` marker with a 24-hour TTL.
- If the job fails, the lock is explicitly removed to allow retries.

This ensures:
- ✅ **Safe concurrency**: In multi-worker environments, only one worker ever processes a job.
- ✅ **Retry resilience**: Failures release the lock so the job can be retried cleanly.
- ✅ **Single-worker compatibility**: Even if you have just one worker, the system behaves correctly with no risk of deadlock or side effects. It also helps in fast pre-checks before doing heavy work.



---

## Configuration

All environment-specific settings are defined in `.env` and loaded through a centralized configuration module (`config/settings.py`). This includes Redis connections, retry strategies, stream names, and default priorities.

### How It Works

- Configuration is injected via `.env` or environment variables.
- Values are parsed using Pydantic settings classes.
- This setup ensures easy overrides in development, testing, or production environments.
- The config layer is designed to evolve — for example, switching to database-driven or remote config management later.

### Example `.env`

```env
REDIS_URL=redis://redis:6379
API_PORT=8000
RETRY_STRATEGY=exponential       # or "fixed"
```
---

## What’s Next

We’ve completed Phase 1. Here’s a roadmap for the upcoming development phases:

### Phase 2 (In Progress – Stable Core Features)
- ✅ **Job Prioritization** – High, medium, and low priority queues (Completed)
- ✅ **Job Cancellation Support** – Ability to cancel in-progress or queued jobs
- ✅ **Dead-letter Queue (DLQ)** – Handle jobs that fail repeatedly
- ✅ **Exponential Backoff Retries** – Gradually increase retry intervals to reduce pressure
- ✅ **Idempotency & Deduplication** – Prevent duplicate job processing
- **Graceful Shutdown** – Cleanly stop workers on termination signals
- **Support for Multiple Queues** – Handle independent job streams
- **Basic Dashboard** – CLI or minimal web UI to view jobs and statuses

### Phase 3 (Planned – Advanced Production-Ready Features)
- **Delayed Job Scheduling** – Enqueue jobs for future execution
- **Horizontal Scaling** – Run multiple worker instances for concurrency
- **Distributed Locking** – Ensure exactly-once processing using Redis Redlock or similar
- **Rate Limiting** – Throttle job processing per job type or tenant
- **Advanced Priority Queues** – Improve control over job ordering and preemption
- **Observability & Metrics** – Add monitoring with Prometheus and Grafana
- **Multi-Tenant Support** – Isolate jobs across users or projects

---

## Technologies Used

- Python
- FastAPI
- Redis Streams
- Docker
- Pydantic
- Uvicorn

---

## Author

[SoeRatch](https://github.com/SoeRatch)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
