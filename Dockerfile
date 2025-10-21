# syntax=docker/dockerfile:1

# Use Python 3.10 slim image for smaller size
FROM python:3.14-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create app user for security (don't run as root)
RUN useradd -m -u 1000 docbt && \
    mkdir -p /app && \
    chown -R docbt:docbt /app

WORKDIR /app

# Copy dependency files and source code
COPY --chown=docbt:docbt pyproject.toml README.md ./
COPY --chown=docbt:docbt src/ ./src/

# Install the package and dependencies as root (needed for system Python)
RUN uv pip install --system -e .

# Switch to docbt user for running the application
USER docbt

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/_stcore/health', timeout=5)"

# Set the entrypoint to run docbt
ENTRYPOINT ["docbt"]
CMD ["run", "--host", "0.0.0.0"]

# --- Multi-stage build for production with optional providers ---
FROM base AS production

# Install optional providers (Snowflake and BigQuery)
USER root
RUN uv pip install --system -e ".[all-providers]"

USER docbt

# --- Development stage with dev tools ---
FROM base AS development

USER root

# Install development dependencies
RUN uv pip install --system -e ".[dev]"

USER docbt

# Override CMD for development (you can run tests, etc.)
CMD ["bash"]
