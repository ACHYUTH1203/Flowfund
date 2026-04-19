# Multi-stage build: compile the React frontend with Node, then bake the
# static output into a Python runtime image that also serves the FastAPI
# backend on the same origin.

# -------- stage 1: frontend build --------
FROM node:20-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


# -------- stage 2: python runtime --------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Poetry for reproducible Python installs.
RUN pip install --no-cache-dir poetry==2.1.4

# Install Python dependencies into the system interpreter (no project venv
# inside the container - we don't need isolation here).
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --without dev

# Backend source.
COPY app/ ./app/
COPY assistant/ ./assistant/
COPY scripts/ ./scripts/

# Built frontend from stage 1 — served at / by FastAPI's StaticFiles mount.
COPY --from=frontend /build/frontend/dist ./frontend/dist

EXPOSE 8000

# On startup: seed the demo DB + FAISS index, then run the server.
# Render (and most hosts) override PORT — fall back to 8000 locally.
CMD python scripts/seed_demo.py \
    && python scripts/seed_rag.py \
    && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
