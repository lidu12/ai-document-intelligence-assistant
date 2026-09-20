# ------------------------------------------------------------------------------
# Production Dockerfile for FastAPI AI Document Intelligence Assistant
# ------------------------------------------------------------------------------

# 1. Base Image: Use official, lightweight Python 3.11 slim variant
FROM python:3.11-slim

# 2. Environment Variables:
# - PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disk
# - PYTHONUNBUFFERED: Forces stdout/stderr output directly to terminal (no log buffering)
# - PYTHONPATH: Ensures imports like 'from app.main import app' resolve from /app root
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 3. Set Working Directory inside the container
WORKDIR /app

# 4. Install System-Level Dependencies:
# - gcc & libpq-dev: Required for compiling asyncpg/psycopg PostgreSQL drivers
# - curl: Required for Docker container health check probes
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Leverage Docker Layer Caching:
# Copy and install dependencies first so code changes don't trigger re-installation
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copy Application Source Code
COPY app ./app

# 7. Security: Create and switch to a non-privileged system user
# Running as root inside a production container is a security risk
RUN addgroup --system appgroup && adduser --system --group appgroup appuser
USER appuser

# 8. Expose Application Port
EXPOSE 8000

# 9. Docker Healthcheck Probe
# Pings /health every 30s to verify server responsiveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 10. Start Command: Launch FastAPI with Uvicorn on 0.0.0.0:8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
