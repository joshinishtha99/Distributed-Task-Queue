# Distributed Task Queue Platform

A production-inspired distributed task queue built from scratch — a simplified
Celery/Sidekiq/SQS — to demonstrate distributed-systems and backend engineering
concepts: Redis-backed queueing, a concurrent worker pool, retries with
exponential backoff, a dead-letter queue, PostgreSQL persistence, a real-time
WebSocket dashboard, and Prometheus/Grafana observability.

## Tech stack
Python 3.12 · FastAPI · Redis · PostgreSQL · SQLAlchemy 2.x · Docker · React/TS

## Local development

1. Copy the environment template and adjust if needed:
   cp .env.example .env

2. Start infrastructure (Postgres + Redis):
   docker compose up -d

3. Install backend dependencies and run the API:
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload

4. Verify: http://localhost:8000/health
