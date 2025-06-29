# Changelog

All notable changes to this project will be documented in this file.

---

## [Phase 3] – Multi-Queue Architecture & Modularization (2025-06-29)

### Added
- Support for **multiple queues** via declarative registration in `queue_registry.py`.
- Per-queue **priority streams**: `high`, `medium`, `low`, and `default`.
- `DisqueueQueue` and `QueueConfig` abstractions for a clean, extensible queue configuration interface.
- `StreamManager` for polling Redis streams based on queue priority.
- `JobProcessor` for orchestrating job execution, including deduplication, retries, and DLQ handling.
- Redis-backed **metadata tracking** (e.g., stream offsets, retry counts).
- New FastAPI route (`/queues/`) to expose registered queue configurations.
- Refactored project structure into modular domains: `core`, `infrastructure`, `api`, `retry`, and `utils`.
- Plugin System – Handlers can now be registered via register_handler(queue_name, handler_fn) for custom job logic per queue.

### Changed
- Refactored `worker.py` to support multiple queues and priority-aware job polling.
- Moved Redis-specific logic to `RedisJobStore` for better separation of infrastructure concerns.
- Streamlined architecture: cleaner boundaries between polling, job processing, and Redis access.

### Fixed
- Renamed `queue.py` to `queue_config.py` to resolve conflict with Python’s built-in `queue` module.

### Upcoming
- Retry Strategy per Queue – Fixed/exponential configurable per queue
- Built-in Job Timeouts – Auto-fail long-running jobs
- Dynamic Queue Registration – Support runtime queue creation via both API and Python interface

---

## [Phase 2] – Core Resilience Features (Completed)

### Added
- Priority support (`high`, `medium`, `low`) within a single queue.
- Job cancellation support and API endpoint.
- Dead-letter queue (DLQ) for failed jobs that exceed retry limits.
- Retry strategy abstraction (`fixed`, `exponential`) via the `retry/` module.
- Redis-based deduplication via decorator to enforce idempotent job execution.
- Graceful shutdown handling for the worker process.

---

## [Phase 1] – Initial Release (Completed)

### Added
- RESTful job API using FastAPI: submit (`/jobs/`), status (`/jobs/{id}`), and cancel (`/jobs/{id}/cancel`).
- Retry mechanism with configurable max attempts (`fixed` strategy).
- Redis Streams as the message broker for job queueing.
- Basic worker loop for polling and processing jobs.
- Dockerized setup with `docker-compose`.