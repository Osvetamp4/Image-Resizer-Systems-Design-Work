# Image-Resizer-Systems-Design-Work
A foundational systems design project that mimics a production-style, distributed, and asynchronous image resizing pipeline. It models a simple user-facing workflow (queue a resize request, poll status, view result) while exercising core backend concepts: queueing, caching, persistence, and metrics.

## Table of contents
- [Project goal](#project-goal)
- [Architecture at a glance](#architecture-at-a-glance)
- [Request flow](#request-flow)
- [Services](#services)
- [API](#api)
- [Storage and caching](#storage-and-caching)
- [Observability](#observability)
- [Frontend UI](#frontend-ui)
- [Cleanup](#cleanup)
- [Repo layout](#repo-layout)

## Project goal
Build a compact, end-to-end system that looks and behaves like a production image processing service. The system is intentionally split into services and uses real infrastructure components (Redis, Postgres, Prometheus, Nginx) to demonstrate async job handling and operational visibility.

## Architecture at a glance
- Client UI served by Nginx
- API (Flask) for enqueueing work and polling status
- Redis queue + cache for task dispatch and fast result lookup
- Worker that resizes images, writes results to shared storage, and persists metadata to Postgres
- Cleanup service that removes expired image files from shared storage
- Prometheus scraping API/worker/Redis metrics

## Request flow
1. User submits image URL + dimensions from the frontend.
2. API checks for a cached result hash in Redis.
3. If cached, API returns the existing task ID; otherwise it queues a new task to Redis.
4. Worker consumes the Redis queue, downloads and resizes the image, writes the file to the shared volume, and stores task metadata in Postgres.
5. API status endpoint reads the result from Redis for fast polling.
6. Cleanup service periodically removes files whose task results have expired from Redis.

## Services
- **nginx**: Serves the static frontend and reverse-proxies API calls.
- **api**: Flask app that queues tasks, tracks status, and exposes Prometheus metrics.
- **redis**: Queue and result cache.
- **worker**: Resizes images, emits metrics, and persists results to Postgres.
- **cleanup_crew**: Periodic cleanup of stale files in the shared volume.
- **postgres**: Persistent storage for task metadata.
- **prometheus**: Metrics collection for API, worker, and Redis exporter.
- **redis_exporter / redis_insight**: Observability tools for Redis.

## API
- `POST /queue-task`: Enqueue a resize job. Expects JSON with `image_url` and `parameters` (`width`, `height`).
- `GET /task-status/<task_id>`: Returns `pending` or a completed result payload.
- `GET /metrics`: Prometheus metrics endpoint for API.
- `GET /health`: Basic health check.

## Storage and caching
- **Redis** stores task queue entries and short-lived task results.
- **Result hashing** avoids duplicate work by caching on `(image_url, width, height)`.
- **Postgres** persists task metadata for long-term audit and analysis.
- **Shared volume** stores resized image files for access by Nginx.

## Observability
- **Prometheus** scrapes API and worker metrics (latency, request counts, task processing time, success/error counts) and Redis exporter stats.
- Worker exposes metrics on port `8000`; API exposes metrics on port `5000`.

## Frontend UI
- Single-page form to submit an image URL and dimensions.
- Polls status until completion, then displays the resized image from the shared volume.

## Demo video
<video controls width="720">
	<source src="./resizer.mp4" type="video/mp4">
	Your browser does not support the video tag.
</video>

## Cleanup
- Background process scans Redis for active task results and removes orphaned files from shared storage.

## Repo layout
- `api/`: Flask API service
- `worker/`: Image processing worker
- `cleanup_crew/`: Cleanup loop for shared storage
- `nginx/`: Nginx config and frontend assets
- `postgres/`: Database initialization SQL
- `prometheus/`: Scrape configuration
- `docker-compose.yml`: Local orchestration for all services
