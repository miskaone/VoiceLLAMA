# VoiceLLAMA Docker Image
# Ultra-fast Text-to-Speech API Server powered by Kokoro-82M
#
# Build: docker build -t voicellama .
# Run:   docker run -p 8333:8333 voicellama
#
# For GPU support, use the GPU target:
# Build: docker build --target gpu -t voicellama:gpu .
# Run:   docker run --gpus all -p 8333:8333 voicellama:gpu

# =============================================================================
# Base stage - common dependencies
# =============================================================================
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash voicellama
WORKDIR /app

# =============================================================================
# Dependencies stage - install Python packages
# =============================================================================
FROM base AS dependencies

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (better layer caching)
COPY pyproject.toml ./
COPY README.md ./
COPY src/voicellama/__init__.py ./src/voicellama/

# Install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[kokoro]"

# =============================================================================
# Production stage - CPU only
# =============================================================================
FROM base AS cpu

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=voicellama:voicellama . .

# Install the application
RUN pip install -e . --no-deps

# Create cache directory for Kokoro model
RUN mkdir -p /home/voicellama/.cache && \
    chown -R voicellama:voicellama /home/voicellama/.cache

# Switch to non-root user
USER voicellama

# Expose port
EXPOSE 8333

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8333/v1/health')" || exit 1

# Default command
CMD ["voicellama", "serve", "--host", "0.0.0.0", "--port", "8333"]

# =============================================================================
# GPU stage - with CUDA support
# =============================================================================
FROM nvidia/cuda:12.1-runtime-ubuntu22.04 AS gpu-base

# Install Python and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN useradd --create-home --shell /bin/bash voicellama
WORKDIR /app

FROM gpu-base AS gpu

# Copy application code
COPY --chown=voicellama:voicellama . .

# Install dependencies with CUDA support
RUN pip install --upgrade pip setuptools wheel && \
    pip install torch --index-url https://download.pytorch.org/whl/cu121 && \
    pip install -e ".[kokoro]"

# Create cache directory for Kokoro model
RUN mkdir -p /home/voicellama/.cache && \
    chown -R voicellama:voicellama /home/voicellama/.cache

# Switch to non-root user
USER voicellama

# Expose port
EXPOSE 8333

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8333/v1/health')" || exit 1

# Default command
CMD ["voicellama", "serve", "--host", "0.0.0.0", "--port", "8333"]

# =============================================================================
# Default target is CPU
# =============================================================================
FROM cpu AS default
