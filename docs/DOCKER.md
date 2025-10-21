# Docker Guide for docbt

This guide explains how to run docbt using Docker.

## Quick Start

### Basic Usage (Base Image)

Run docbt with default settings:

```bash
docker build -t docbt:latest .
docker run -p 8501:8501 docbt:latest
```

Access the app at: http://localhost:8501

### Using Docker Compose (Recommended)

```bash
# Run base version
docker-compose up docbt

# Run production version with all providers
docker-compose --profile production up docbt-production

# Run development version
docker-compose --profile dev up docbt-dev
```

## Docker Images

### Base Image (`base`)
- **Size**: ~500MB
- **Includes**: Core docbt functionality
- **Use case**: Basic file-based workflows without cloud connectors

### Production Image (`production`)
- **Size**: ~800MB  
- **Includes**: Core + Snowflake + BigQuery connectors
- **Use case**: Production deployments with cloud data warehouses

### Development Image (`development`)
- **Size**: ~900MB
- **Includes**: Everything + dev tools (pytest, ruff, pre-commit)
- **Use case**: Local development and testing

## Configuration

### Environment Variables

Create a `.env` file in the same directory as `docker-compose.yml`:

```env
# OpenAI Configuration
DOCBT_OPENAI_API_KEY=sk-your-api-key-here

# LM Studio (running on host)
DOCBT_LMSTUDIO_HOST=host.docker.internal
DOCBT_LMSTUDIO_PORT=1234

# Ollama (running on host)
DOCBT_OLLAMA_HOST=host.docker.internal
DOCBT_OLLAMA_PORT=11434

# Snowflake
DOCBT_SNOWFLAKE_ACCOUNT=your-account
DOCBT_SNOWFLAKE_USER=your-user
DOCBT_SNOWFLAKE_PASSWORD=your-password
DOCBT_SNOWFLAKE_WAREHOUSE=your-warehouse
DOCBT_SNOWFLAKE_DATABASE=your-database
DOCBT_SNOWFLAKE_SCHEMA=your-schema

# BigQuery
# Mount your GCP credentials JSON file and set:
# DOCBT_GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-key.json
```

### Volumes

Mount directories for data and credentials:

```yaml
volumes:
  # For file uploads
  - ./data:/app/data

  # For GCP credentials
  - ./credentials:/app/credentials:ro
```

## Building Custom Images

### Build specific target:

```bash
# Base image
docker build --target base -t docbt:base .

# Production image
docker build --target production -t docbt:production .

# Development image
docker build --target development -t docbt:dev .
```

### Build with build arguments:

```bash
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t docbt:3.11 \
  .
```

## Networking

### Accessing Local LLM Servers

If you're running Ollama or LM Studio on your host machine:

#### Option 1: Use host.docker.internal (Recommended)

The docker-compose.yml already includes:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Set environment variables:
```env
DOCBT_OLLAMA_HOST=host.docker.internal
DOCBT_LMSTUDIO_HOST=host.docker.internal
```

#### Option 2: Use host network mode (Linux only)

```yaml
network_mode: host
```

#### Option 3: Use host IP address

Find your host IP:
```bash
# Linux/macOS
ifconfig | grep "inet "

# Windows
ipconfig
```

Set environment variables:
```env
DOCBT_OLLAMA_HOST=192.168.1.100
DOCBT_LMSTUDIO_HOST=192.168.1.100
```

## Examples

### Example 1: Run with OpenAI

```bash
docker run -p 8501:8501 \
  -e DOCBT_OPENAI_API_KEY=sk-your-key \
  -e DOCBT_LLM_PROVIDER_DEFAULT=openai \
  docbt:latest
```

### Example 2: Run with Local LM Studio

```bash
docker run -p 8501:8501 \
  -e DOCBT_LMSTUDIO_HOST=host.docker.internal \
  -e DOCBT_LMSTUDIO_PORT=1234 \
  -e DOCBT_LLM_PROVIDER_DEFAULT=lmstudio \
  --add-host host.docker.internal:host-gateway \
  docbt:latest
```

### Example 3: Run with Snowflake

```bash
docker run -p 8501:8501 \
  -e DOCBT_SNOWFLAKE_ACCOUNT=your-account \
  -e DOCBT_SNOWFLAKE_USER=your-user \
  -e DOCBT_SNOWFLAKE_PASSWORD=your-password \
  -e DOCBT_SNOWFLAKE_WAREHOUSE=your-warehouse \
  -e DOCBT_DATA_SOURCE_DEFAULT=snowflake \
  docbt:production
```

### Example 4: Run with mounted data directory

```bash
docker run -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  docbt:latest
```

### Example 5: Development with hot reload

```bash
docker run -p 8501:8501 \
  -v $(pwd):/app \
  -e DOCBT_DEVELOPER_MODE_ENABLED=True \
  docbt:dev
```

## Troubleshooting

### Cannot connect to LM Studio/Ollama

1. Verify the service is running on host:
   ```bash
   curl http://localhost:1234/api/v0/models  # LM Studio
   curl http://localhost:11434/api/tags      # Ollama
   ```

2. Check if host.docker.internal resolves:
   ```bash
   docker run --rm --add-host host.docker.internal:host-gateway \
     docbt:latest python -c "import socket; print(socket.gethostbyname('host.docker.internal'))"
   ```

3. Try using host IP instead of host.docker.internal

### Permission errors with volumes

```bash
# Fix ownership
sudo chown -R 1000:1000 ./data ./credentials

# Or run with your user ID
docker run --user $(id -u):$(id -g) ...
```

### Container exits immediately

Check logs:
```bash
docker logs docbt
docker-compose logs docbt
```

### BigQuery authentication issues

Ensure your GCP credentials JSON is mounted correctly:
```yaml
volumes:
  - ./path/to/gcp-key.json:/app/credentials/gcp-key.json:ro
environment:
  - DOCBT_GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-key.json
```

## Production Deployment

### Using Docker Compose in Production

```bash
# Start in detached mode
docker-compose --profile production up -d

# View logs
docker-compose logs -f docbt-production

# Stop
docker-compose --profile production down
```

### Health Checks

The container includes a health check:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' docbt

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' docbt
```

### Resource Limits

Add to docker-compose.yml:

```yaml
services:
  docbt:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Security Best Practices

1. **Use secrets for sensitive data:**
   ```yaml
   secrets:
     openai_api_key:
       file: ./secrets/openai_key.txt
   services:
     docbt:
       secrets:
         - openai_api_key
   ```

2. **Run as non-root user** (already configured)

3. **Use read-only volumes for credentials:**
   ```yaml
   volumes:
     - ./credentials:/app/credentials:ro
   ```

4. **Scan images for vulnerabilities:**
   ```bash
   docker scan docbt:latest
   ```

## Updating

```bash
# Pull latest code
git pull

# Rebuild image
docker-compose build docbt

# Restart with new image
docker-compose up -d docbt
```

## Cleaning Up

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi docbt:latest docbt:production docbt:dev

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Clean up unused images
docker image prune -a
```
