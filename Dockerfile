# File: /Dockerfile
# Description: Docker image for MyRAGDB production deployment
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/logs && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser config/ config/
COPY --chown=appuser:appuser scripts/ scripts/

# Switch to app user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3002/api/v1/health || exit 1

# Expose port
EXPOSE 3002

# Run application
CMD ["python", "-m", "myragdb.api.server"]
