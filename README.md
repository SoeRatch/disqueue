# Disqueue

**Disqueue** is a minimal, lightweight distributed job queue system inspired by Celery and BullMQ, built using FastAPI, Redis Streams, and Docker. It allows you to queue background jobs, track their status, and retry on failure — all while keeping things simple and easy to reason about.

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
- Failed jobs are retried up to a max retry limit and then moved to a Dead-letter Queue (DLQ).
- FastAPI provides endpoints to submit and query jobs.
- Cancelled jobs are marked with cancelled status and skipped by workers, while maintaining stream offsets to avoid reprocessing.

---

## Components

### `api/` – FastAPI Service
- POST `/jobs/` to submit a job with payload and priority.
  
### `worker/worker.py` – Worker Process
- Continuously reads from Redis Streams (`XREAD`).
- Enforces priority: high → medium → low .
- Persists `last_id` per stream to avoid duplication.
- Skips jobs marked as cancelled and safely moves past them by updating the stream offset.

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
├── worker/
│   └── worker.py        # Worker process to handle jobs
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
- Retries are capped at a configurable `MAX_RETRIES` (default: 3).
- Once retries are exhausted, the job is marked as `failed`.

---



## Dead-letter Queue (DLQ)

Jobs that exceed the maximum retry limit are automatically moved to a **Dead-letter Queue** (`job:dlq`) for post-mortem analysis.

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

## Configuration

Environment configuration is managed through `.env` and `config/settings.py`.

`.env`:

```
REDIS_URL=redis://redis:6379
API_PORT=8000
```

`config/settings.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    job_stream_high: str = "job_stream_high"
    job_stream_medium: str = "job_stream_medium"
    job_stream_low: str = "job_stream_low"
    job_status_hash: str = "job_status"
    job_retry_hash: str = "job_retries"
    max_retries: int = 3
    default_priority: str = "medium"
    job_last_ids_hash: str = "job_last_ids"

    class Config:
        env_file = ".env"

settings = Settings()
```
---

## What’s Next

We’ve completed Phase 1. Here’s a roadmap for the upcoming development phases:

### Phase 2 (In Progress – Stable Core Features)
- ✅ **Job Prioritization** – High, medium, and low priority queues (Completed)
- ✅ **Job Cancellation Support** – Ability to cancel in-progress or queued jobs
- ✅ **Dead-letter Queue (DLQ)** – Handle jobs that fail repeatedly
- **Exponential Backoff Retries** – Gradually increase retry intervals to reduce pressure
- **Idempotency & Deduplication** – Prevent duplicate job processing
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
