# Build stage
FROM python:3.9-slim AS builder

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with fallback mechanism for MCP SDK
RUN pip install --no-cache-dir --upgrade pip && \
    # Try to install MCP from PyPI first
    pip install --no-cache-dir "mcp[cli]>=0.4.0,<0.5.0" || \
    echo "Failed to install MCP from PyPI, will try local path if available" && \
    # Install other dependencies
    grep -v "mcp" requirements.txt > requirements_without_mcp.txt && \
    pip install --no-cache-dir -r requirements_without_mcp.txt

# Attempt to copy and install local MCP SDK if it exists
RUN mkdir -p /tmp/mcp-python-sdk
# Use shell scripting to handle the copy conditionally
RUN if [ -d "mcp-python-sdk" ]; then \
        cp -r mcp-python-sdk/* /tmp/mcp-python-sdk/ || true; \
    else \
        echo "No local MCP SDK found, using PyPI version if available"; \
    fi
RUN if [ -f "/tmp/mcp-python-sdk/setup.py" ]; then \
        pip install --no-cache-dir -e "/tmp/mcp-python-sdk/[cli]"; \
    fi

# Runtime stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    APP_ENV=prod \
    APP_VERSION=1.0.0

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy application code
COPY server.py google_ads_client.py health.py config.py ./
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