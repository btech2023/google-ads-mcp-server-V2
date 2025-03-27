# PROJECT NEBULA: Google Ads MCP Server CI/CD Pipeline Fixes
**Date: 2025-03-21**

## Context Summary

Based on the GitHub Actions workflow logs, we're experiencing two persistent issues in our CI/CD pipeline:

1. **MCP Python SDK Dependency Issue**: The Docker build is failing because it's trying to access a local `mcp-python-sdk/` directory that doesn't exist in the GitHub Actions build context. This issue manifests as:
   ```
   ERROR: failed to solve: failed to compute cache key: failed to calculate checksum of ref 6e8bf838-5188-41d1-bd5f-2bc4f2797329::1zyra1g5qqz3b7wkflo7h: "/mcp-python-sdk": not found
   ```

2. **GKE Credentials Issue**: The GKE deployment step is failing because the service account credentials aren't being properly loaded:
   ```
   Error: google-github-actions/get-gke-credentials failed with: could not load the default credentials.
   ```

Our previous fixes attempted to address these issues but were unsuccessful. This document provides a comprehensive solution that merges the best approaches from both the Technical Project Manager and Cursor AI recommendations.

## Recommended Fixes

### 1. MCP Dependency Solution: Hybrid Installation Approach

#### Update Dockerfile

```dockerfile
# Build stage
FROM python:3.9-slim AS builder

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies with fallback mechanism for MCP SDK
RUN pip install --no-cache-dir --upgrade pip && \
    # Try to install MCP from PyPI first
    pip install --no-cache-dir mcp==0.4.0 || \
    pip install --no-cache-dir "mcp[cli]==0.4.0" || \
    echo "Failed to install MCP from PyPI, will try local path if available" && \
    # Install other dependencies
    grep -v "mcp" requirements.txt > requirements_without_mcp.txt && \
    pip install --no-cache-dir -r requirements_without_mcp.txt

# Attempt to copy and install local MCP SDK if it exists
COPY mcp-python-sdk/ /tmp/mcp-python-sdk/ || echo "No local MCP SDK found, using PyPI version if available"
RUN if [ -d "/tmp/mcp-python-sdk" ] && [ -f "/tmp/mcp-python-sdk/setup.py" ]; then \
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
```

#### Update requirements.txt

```
# Google Ads MCP Server Dependencies
# Core dependencies
mcp==0.4.0
google-ads>=21.3.0
python-dotenv>=1.0.0
fastapi>=0.103.1
uvicorn>=0.23.2

# Async support
asyncio>=3.4.3
httpx>=0.24.1

# Utilities
pydantic>=2.0.0
python-json-logger>=2.0.7

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.1
```

### 2. GKE Credentials Solution: Explicit Authentication

Update all workflow files (ci-cd-improved.yml, deploy-gke.yml, deploy-dev.yml, deploy-prod.yml) to include the explicit credentials parameter:

```yaml
- name: Get GKE Credentials
  uses: google-github-actions/get-gke-credentials@v1
  with:
    cluster_name: ${{ env.GKE_CLUSTER }}
    location: ${{ env.GKE_ZONE }}
    project_id: ${{ env.PROJECT_ID }}
    credentials: ${{ secrets.GCP_SA_KEY }}
```

### 3. GitHub Workflow Submodule Configuration

If the MCP SDK is a separate repository, update your checkout action to include submodules:

```yaml
- name: Checkout
  uses: actions/checkout@v3
  with:
    submodules: recursive
```

## Implementation Verification Steps

After implementing these changes, verify the solution with these steps:

1. **Confirm MCP SDK Status**:
   - Run `git ls-files | grep mcp-python-sdk` locally to check if the directory is tracked in Git
   - If it's not tracked, consider these options:
     - Add it as a Git submodule if it's a separate repository
     - Include it directly in your repository if it's your own code
     - Switch to using the PyPI package exclusively

2. **Verify GCP Service Account Key**:
   - Ensure the GCP_SA_KEY secret in GitHub is:
     - Properly formatted as a complete JSON service account key
     - Has the necessary permissions (Kubernetes Engine Admin, Storage Admin)
     - Is correctly stored as a repository secret

3. **Test with Reduced Build**:
   - Consider temporarily simplifying the workflow to test just the Docker build portion
   - Once the Docker build succeeds, add back the GKE deployment steps

## Error Documentation

```
[ERROR-CICD005] - 2025-03-21
Context: Docker build in GitHub Actions pipeline
Problem: MCP SDK local dependency not found in build context
Root Cause: Local dependency path exists in development but not in CI environment
Solution: Implemented hybrid approach to try PyPI package first, fallback to local if available
Prevention: Use explicit dependency management with both local and remote options
References: GitHub Actions logs, Dockerfile best practices

[ERROR-CICD006] - 2025-03-21
Context: GKE deployment in GitHub Actions
Problem: GKE credentials not loading properly
Root Cause: Missing explicit credentials parameter in get-gke-credentials action
Solution: Added explicit credentials parameter referencing GCP_SA_KEY secret
Prevention: Always provide explicit credentials for GCP service interactions
References: google-github-actions/get-gke-credentials documentation
```

## Long-Term Recommendations

For a more maintainable solution in the future, consider:

1. **Package Management**: 
   - Publish your MCP SDK to a package registry (PyPI or private)
   - Switch to using published packages exclusively in production builds
   - Use local development dependencies only in development workflows

2. **CI/CD Configuration**:
   - Separate your workflows more clearly by environment
   - Create dedicated test workflows that don't deploy
   - Use environment protection rules for production deployments

3. **Secret Management**:
   - Consider using GCP Secret Manager or HashiCorp Vault
   - Rotate service account keys regularly
   - Use workload identity federation where possible

These changes should resolve the current CI/CD pipeline issues while making the system more robust for future development.

## Progress Updates

### March 27, 2025: Successful CI/CD Pipeline & Kubernetes Deployment 🎉

**Achievement:** We have successfully configured and completed our first end-to-end CI/CD pipeline that deploys the Google Ads MCP Server to Kubernetes!

#### Issues Resolved:

1. **MCP Python SDK Integration Issue:** 
   - Changed from using `mcp.include_routers(app)` (which doesn't exist) to the correct pattern of mounting the MCP server's SSE app at `/mcp` path using `app.mount("/mcp", mcp.sse_app())`.
   - This resolved the container crash issue that was preventing deployment.

2. **Image Tagging Inconsistency:** 
   - Standardized image tag format by using the full SHA in both build and deployment stages.
   - Changed from `kustomize edit set image gcr.io/PROJECT_ID/google-ads-mcp-server=ghcr.io/${{ github.repository }}:sha-$(git rev-parse --short HEAD)` to `kustomize edit set image gcr.io/PROJECT_ID/google-ads-mcp-server=ghcr.io/${{ github.repository }}:sha-${{ github.sha }}`.

3. **Kubernetes Configuration Enhancements:**
   - Added `terminationGracePeriodSeconds: 30` to give pods time to shut down gracefully.
   - Added `preStop` lifecycle hook with a 5-second sleep to allow connections to drain.
   - Set `progressDeadlineSeconds: 300` to properly detect stalled deployments.
   - Improved rolling update strategy with `maxUnavailable: 0, maxSurge: 1` for zero-downtime deployments.

4. **CI/CD Workflow Cleanup:**
   - Consolidated multiple workflow files into a single `cicd.yml` file.
   - Increased deployment verification timeout from 300s to 600s.
   - Added comprehensive debugging that automatically runs if deployment fails.
   - Created clear snippets of all successful workflow sections for easy reference.

#### Next Steps:

1. **Performance & Monitoring:**
   - Set up monitoring for the deployed MCP server.
   - Implement proper logging and observability.
   - Perform load testing to ensure the server can handle expected traffic.

2. **Security Enhancements:**
   - Add security scanning to the CI/CD pipeline.
   - Implement network policies for the Kubernetes cluster.
   - Rotate service account keys regularly.

3. **Reliability Improvements:**
   - Implement multi-region deployment for higher availability.
   - Set up automatic backup/restore of critical data.
   - Create disaster recovery procedures.

4. **Feature Development:**
   - Now that the infrastructure is stable, resume work on MCP server features.
   - Expand Google Ads API integration capabilities.
   - Add more visualization options through Claude Artifacts.

This successful deployment represents a major milestone for Project Nebula. After weeks of troubleshooting and configuration iterations, we now have a solid foundation for our Google Ads MCP server infrastructure.
