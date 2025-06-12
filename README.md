# Disqueue

**Disqueue** is a minimal, lightweight distributed job queue system inspired by Celery and BullMQ, built using FastAPI, Redis Streams, and Docker. It allows you to queue background jobs, track their status, and retry on failure — all while keeping things simple and easy to reason about.

---
## Table of Contents

- [Features](#features)  
- [Stack](#stack)  
- [Directory Structure](#directory-structure)  
- [Getting Started](#getting-started)  
  - [Prerequisites](#prerequisites)  
  - [Setup Instructions](#setup-instructions)  
- [Usage](#example-usage)  
  - [Queue a Job](#1-queue-a-job)  
  - [Check Job Status](#2-check-job-status)  
  - [Simulate a Failing Job](#3-simulate-a-failing-job)  
- [Retry Mechanism](#retry-mechanism)  
- [Configuration](#configuration)  
- [What’s Next](#whats-next) 
- [Technologies Used](#technologies-used)  
- [Author](#author)  
- [License](#license)

---

## Features

- **Job Submission**: Submit jobs via a REST API to queue jobs.
- **Status Tracking**: Monitor job statuses (`queued`, `in_progress`, `retrying`, `completed`, `failed`).
- **Redis Integration**: Utilizes Redis Streams and Hashes for job management.
- **Retry Mechanism**: Automatic retries for failed jobs up to a configurable maximum.
- **Dockerized Environment**: Consistent and portable development setup.

---

## Stack

- **FastAPI** - for REST APIs
- **Redis Streams** - as a message queue
- **Docker** & **Docker Compose** - for local dev & containerization
- **Python** - core language for API & worker

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

```bash
curl -X POST http://localhost:8000/jobs/ \
     -H "Content-Type: application/json" \
     -d '{"payload": {"task": "test"}}'
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
     -d '{"payload": {"fail": true}}'
```

The system will retry the job up to the `MAX_RETRIES` limit.

---

## Retry Mechanism

- If a job fails (e.g., the payload contains `"fail": true`), the system retries it.
- Retries are capped at a configurable `MAX_RETRIES` (default: 3).
- Once retries are exhausted, the job is marked as `failed`.

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
    REDIS_URL: str
    job_stream: str = "job_stream"
    job_status_hash: str = "job_status"
    job_retry_hash: str = "job_retries"
    max_retries: int = 3

    class Config:
        env_file = ".env"

settings = Settings()
```
---

## What’s Next

We’ve completed Phase 1. Here’s a roadmap for the upcoming development phases:

### Phase 2 (Stable features)
- **Job Prioritization**
- **Job Cancellation Support**
- **Dead-letter queue (DLQ)** for jobs that repeatedly fails.
- **Exponential backoff retries** to avoid hammering systems.
- **Idempotency & deduplication** to prevent duplicate processing.
- **Graceful shutdown** and signal handling to cleanly stop workers.
- **Support for multiple queues**
- **Basic dashboard** (CLI or minimal UI) to inspect jobs and statuses.

### Phase 3 (Advanced production-ready features)
- **Scheduling/delayed jobs** – enqueue for future execution
- Horizontal **scaling** (run multiple worker replicas)
- **Distributed locking** (e.g., via Redis Redlock) for exactly-once delivery
- **Rate limiting** per job type or tenant
- **Priority queues** to process high-level jobs first
- **Observability & metrics** (Prometheus, Grafana)
- **Multi-tenant support** for isolating workloads across users/projects

---

## Technologies Used

- Python
- FastAPI
- Redis Streams
- Docker / Docker Compose
- Pydantic
- Uvicorn

---

## Author

[SoeRatch](https://github.com/SoeRatch)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
