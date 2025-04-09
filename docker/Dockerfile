# Build stage
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Install git (needed for GitHub installation)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with all requirements including MCP from GitHub
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    APP_ENV=prod \
    APP_VERSION=1.0.0

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy application code
COPY server.py google_ads_client.py health.py config.py monitoring.py ./
COPY .env.example ./.env.example
COPY scripts ./scripts
COPY test_*.py ./

# Create directory for logs
RUN mkdir -p /var/log/google-ads-mcp

# Create a non-root user
RUN adduser --disabled-password --gecos "" mcp-user && \
    chown -R mcp-user:mcp-user /app /var/log/google-ads-mcp

# Switch to non-root user
USER mcp-user

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import http.client; conn = http.client.HTTPConnection('localhost:${PORT}'); conn.request('GET', '/health'); resp = conn.getresponse(); exit(0 if resp.status == 200 else 1)" || exit 1

# Launch the server
CMD ["python", "server.py"] 