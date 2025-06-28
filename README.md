# Disqueue

**Disqueue** is a lightweight distributed job queue system inspired by Celery and BullMQ. Built with FastAPI, Redis Streams, and Docker, it supports job prioritization, retries, cancellation, dead-letter queue and Redis-powered idempotency and deduplication — all while remaining modular, extensible, and developer-friendly.

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

- **Multiple Queues** – Register and manage multiple job queues declaratively.
- **Priority Handling** – Supports `high`, `medium`, `low` and `default` priority job queues.
- **Retry Mechanism** – Automatic retries with configurable strategy and limits.
- **Dead-letter Queue (DLQ)** – Failed jobs are automatically moved to a DLQ after exceeding retry limit for inspection or manual retry.
- **Job Cancellation** – Cancel jobs before they are processed by a worker.
- **Idempotency & Deduplication** – Redis-powered lock mechanism ensures a job is never processed by more than one worker simultaneously.
- **Graceful Shutdown** – Worker completes the current job cleanly on SIGINT/SIGTERM.
- **Redis Integration** – Uses Redis Streams and Hashes for job management.
- **Dockerized** – Easily reproducible local development environment.
- **FastAPI API Layer** – REST interface for job submission, status, cancellation, and queue discovery.
- **Modular Design** – Decoupled architecture for clean separation of concerns.
- **Easily Extensible** – Designed with modularity in mind to support open-source growth.

---

## Stack

- **FastAPI** – REST API framework.
- **Redis Streams** – Message broker.
- **Python** – Worker logic and APIs.
- **Docker & Docker Compose** – Containerization.
- **Pydantic** – Typed settings and schema validation.


---

## Architecture Overview

- Jobs are added to Redis Streams based on queue name and priority.
- Job metadata (status, retry count, last stream ID, etc.) is tracked in Redis Hashes.
- Workers poll queues using a configurable priority order.
- Deduplication ensures only one worker processes a job at a time.
- Failed jobs are retried up to a max retry limit, and moved to DLQ after retries exceed limit.
- Each worker is aware of multiple queues and priorities using a central registry.
- Cancelled jobs are acknowledged to maintain stream offsets and avoid reprocessing.
- Worker logic is modularized via a StreamManager (stream polling) and JobProcessor (execution, retries, DLQ, deduplication).
- Workers support **graceful shutdown**, completing the in-progress job before exiting.

---

## Components

### `api/` – FastAPI Service
- POST `/jobs/` – Submit jobs with payload, priority, and queue.
- GET `/jobs/{job_id}` – Check status of a specific job.
- POST `/jobs/{job_id}/cancel` – Cancel a job if it's still queued or retrying.
- GET `/queues/` – List registered queues and configurations.

### `core/worker.py` – Main Worker Loop
- Loads all registered queues and initializes `QueueStreamManager`.
- Delegates job execution to `JobProcessor`.
- Supports safe exit on shutdown signal.

### `core/queue_config.py` – Queue Registration
- Declarative queue registration via config.
- Central registry supports multiple named queues with custom priority schemes.

### `core/stream_manager.py` – QueueStreamManager
- Reads from Redis streams using `XREAD`.
- Manages stream offset tracking (`last_id`).
- Polls in priority order.

### `core/processor.py` – JobProcessor
- Core job logic:
  - Deduplication
  - Status updates
  - Retry handling
  - DLQ fallback

### `infrastructure/redis_job_store.py`
- Redis interface for enqueueing, job status, metadata, and stream tracking.
- Used by `JobProcessor` and `QueueStreamManager`.

### `utils/deduplication.py`
- Provides a `@deduplicated()` decorator using Redis `SET NX` locks.
- Ensures only the first worker to acquire the lock processes the job.
- Automatically releases the lock on failure or marks it `done` on success.

---

## Directory Structure

```
disqueue/
├── api/
│   ├── main.py               # FastAPI entry point
│   ├── models.py             # Request/response schemas
│   └── routes/
│       ├── job_routes.py     # Job-related API endpoints
│       └── queue_routes.py   # Queue-related API endpoints
├── config/
│   ├── logging_config.py     # Sets up logging format and levels
│   ├── queue_registry.py     # Declares and registers supported queues and priorities
│   └── settings.py           # Loads env vars and app settings via Pydantic
├── core/
│   ├── processor.py          # Core job logic: retry, DLQ, status, deduplication
│   ├── queue_config.py       # Models for queue configs used by registry
│   ├── registry.py           # Central place for accessing registered queues
│   ├── status.py             # Status enum and helpers
│   ├── stream_manager.py     # Polls Redis Streams in priority order
│   └── worker.py             # Main worker loop and graceful shutdown logic
├── infrastructure/
│   ├── redis_conn.py         # Sets up Redis connection
│   └── redis_job_store.py    # Abstractions for enqueuing, tracking, and DLQ
├── retry/
│   ├── factory.py            # Returns retry strategy instance based on config
│   └── strategies.py         # Fixed and exponential retry implementations
├── utils/
│   └── deduplication.py      # Redis lock decorator to prevent duplicate execution
├── .env.example
├── requirements.txt
├── Dockerfile.api
├── Dockerfile.worker
├── docker-compose.yml
└── README.md
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
    
    Visit the API: [http://localhost:8000/docs](http://localhost:8000/docs)
  
4. **(Optional) Extend Worker Shutdown Timeout**:
    To prevent Docker from force-killing the worker while it’s processing a job, you can extend the shutdown grace period in `docker-compose.yml`:

    ```yaml
    services:
      worker:
        stop_grace_period: 90s
    ```

---

## Example Usage

### 1. Queue a Job:

  ```bash
  curl -X POST http://localhost:8000/jobs/ \
      -H "Content-Type: application/json" \
      -d '{
           "queue_name": "default",
           "priority": "high",
           "payload": {"msg": "process this"}
         }'
  ```
  ```bash
  curl -X POST http://localhost:8000/jobs/ \
      -H "Content-Type: application/json" \
      -d '{
           "queue_name": "image_processing",
           "priority": "low",
           "payload": {"msg": "low priority message from queue - image_processing"}
         }'
  ```

### 2. Check Job Status:

```bash
curl http://localhost:8000/jobs/<job_id>
```

### 3. Simulate a Failing Job:
```bash

curl -X POST http://localhost:8000/jobs/ \
     -H "Content-Type: application/json" \
     -d '{
           "queue_name": "image_processing",
           "priority": "high",
           "payload": {"fail": true}
         }'
```
> This simulates a failure, and the system retries the job according to the configured strategy.

### 4. Cancel a Queued Job:
```bash
curl -X POST http://localhost:8000/jobs/<job_id>/cancel
```
> Cancels a job that is either queued or retrying.

### 5. Discover Registered Queues

```bash
curl http://localhost:8000/queues/
```
---

## Retry Mechanism
- Retries are triggered on exceptions.
- Configurable via `.env`.
- Two retry strategies are supported:
  - **fixed**: Retry after a constant delay (e.g., 1 second).
  - **exponential**: Retry after increasing delays (e.g., 1s → 2s → 4s → 8s).
- Retry attempts are tracked via `job_retries:{job_id}` in Redis.
- Once retries are exhausted, the job moves to the DLQ.

---



## Dead-letter Queue (DLQ)

Jobs that exceed the maximum retry limit are moved to a Redis Stream called `job:dlq` for post-mortem analysis.

Each DLQ message includes:
- `job_id`
- `payload`
- `reason`

You can inspect the DLQ via Redis CLI:

```bash
# In Redis CLI (local)
127.0.0.1:6379> XRANGE job:dlq - +
```
---

## Idempotency & Deduplication

In distributed queue systems, it’s common for the same job to be picked up more than once — either due to retries, network glitches, or multiple workers competing. Disqueue avoids this using a Redis-based locking mechanism via a reusable decorator.

The core logic is defined in `utils/deduplication.py` and applied to the job processor in `core/processor.py`:

```python
# core/worker.py

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
- On success, mark `done` with a 24-hour TTL.
- On failure, the lock is explicitly removed to allow retries.

This ensures:
- ✅ **Safe concurrency**: In multi-worker environments, only one worker ever processes a job.
- ✅ **Retry resilience**: Failures release the lock so the job can be retried cleanly.
- ✅ **Single-worker compatibility**: Even if you have just one worker, the system behaves correctly with no risk of deadlock or side effects. It also helps in fast pre-checks before doing heavy work.



---

## Configuration

- Defined via `.env` and loaded using Pydantic in `config/settings.py`.

### Example
```env
REDIS_URL=redis://redis:6379
API_PORT=8000
RETRY_STRATEGY=exponential
```

---

## What’s Next

### ✅ Phase 2 – Stable Core Features (Completed)
- ✅ **Job Prioritization** 
- ✅ **Job Cancellation Support**
- ✅ **Dead-letter Queue (DLQ)**
- ✅ **Exponential Backoff Retries**
- ✅ **Pluggable Retry Strategies**
- ✅ **Idempotency & Deduplication**
- ✅ **Graceful Shutdown**

We’ve completed Phase 1 and Phase 2. Here’s a roadmap for the upcoming development phases:

### Phase 3 - Multi-Queue Architecture (In Progress)

- ✅ **Declarative Queue Registry**
- ✅ **Multi-queue + multi-priority support**
- ✅ **Modular refactor (`JobProcessor`, `StreamManager`)**
- ✅ **Enhanced API extensibility**

### Phase 4 – Advanced Features (Planned)
- **Plugin system for jobs**
- **Delayed Job Scheduling**
- **Rate Limiting**
- **Distributed Locking (Redlock)**
- **Metrics (Prometheus)**
- **CLI / Dashboard**
- **Horizontal Scaling**
- **Multi-Tenant Support**

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

> Contributions welcome — feel free to open issues or PRs!
