#!/usr/bin/env python
"""
Google Ads MCP Server

This server exposes Google Ads API functionality through the Model Context Protocol (MCP).
"""

import os
import json
import logging
import uuid
import asyncio
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from google_ads_mcp_server.google_ads.client import GoogleAdsService
from google_ads_mcp_server.google_ads.client_base import GoogleAdsClientError
from google_ads_mcp_server.health import health_check
from google_ads_mcp_server.db.manager import SQLiteDatabaseManager

from google_ads_mcp_server.auth import get_current_user

# Import utility modules
from google_ads_mcp_server.utils.token_utils import hash_token, verify_token
from google_ads_mcp_server.utils.error_handler import (
    handle_exception,
    create_error_response,
    ErrorDetails,
    SEVERITY_ERROR,
    CATEGORY_SERVER,
)
from google_ads_mcp_server.utils.logging import (
    log_api_call,
    log_mcp_request,
    get_logger,
)

from google_ads_mcp_server.mcp.tools import register_tools

# Get logger
logger = get_logger("google-ads-mcp")

# Create request ID context
_request_id_context = {}


def get_current_request_id():
    """Get the current request ID from context."""
    task = asyncio.current_task()
    if task is None:
        return None
    return _request_id_context.get(task.get_name())


@asynccontextmanager
async def set_request_context(request_id):
    """Set the request ID in the context for the current task."""
    task = asyncio.current_task()
    if task is not None:
        task_name = task.get_name()
        _request_id_context[task_name] = request_id
        try:
            yield
        finally:
            if task_name in _request_id_context:
                del _request_id_context[task_name]
    else:
        yield


# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Initialize the MCP server
mcp = FastMCP(
    "Google Ads MCP Server",
    description="A server that provides access to Google Ads data through the Model Context Protocol",
)

# Create FastAPI app for HTTP endpoints (like health checks)
app = FastAPI(title="Google Ads MCP Server API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add a unique request ID to each request for tracing."""
    request_id = str(uuid.uuid4())

    # Set the request ID in the context for this task
    async with set_request_context(request_id):
        try:
            # Process the request
            response = await call_next(request)
            # Add the request ID to the response headers
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as e:
            # Handle exceptions with our error handler
            error_details = handle_exception(
                e,
                context={"path": request.url.path, "method": request.method},
                severity=SEVERITY_ERROR,
                category=CATEGORY_SERVER,
            )

            # Create a standardized error response
            error_response = create_error_response(error_details)

            # Return as JSON response with appropriate status code
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR
            if isinstance(e, HTTPException):
                status_code = e.status_code

            return JSONResponse(status_code=status_code, content=error_response)


# Initialize monitoring if enabled
if os.environ.get("ENABLE_METRICS", "false").lower() == "true":
    try:
        from monitoring import init_monitoring

        logger.info("Initializing monitoring...")
        init_monitoring(app)
    except ImportError as e:
        logger.warning(f"Monitoring module not available: {str(e)}")
    except Exception as e:
        error_details = handle_exception(e, context={"component": "monitoring"})
        logger.error(f"Failed to initialize monitoring: {error_details.message}")

# Mount the MCP's SSE app to the FastAPI app at the /mcp path
app.mount("/mcp", mcp.sse_app())


# HTTP health check endpoint for container probes
@app.get("/health")
async def http_health_check():
    """HTTP endpoint for health checks, used by container probes."""
    try:
        health_data = await health_check.get_health()
        if health_data["status"] == "OK":
            return health_data
        return JSONResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE, content=health_data
        )
    except Exception as e:
        error_details = handle_exception(
            e, context={"endpoint": "/health"}, category=CATEGORY_SERVER
        )
        logger.error(f"Health check failed: {error_details.message}")
        return JSONResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            content={"status": "ERROR", "message": error_details.message},
        )


@app.get("/whoami")
async def whoami(user: Dict = Depends(get_current_user)):
    """Return information about the authenticated user."""
    return {"user": user}


# Register tools from the mcp.tools module
try:
    logger.info("Registering MCP tools...")
    google_ads_service = GoogleAdsService()
    register_tools(mcp, google_ads_service)
    logger.info("MCP tools registered successfully")
except Exception as e:
    error_details = handle_exception(
        e, context={"component": "tool_registration"}, category=CATEGORY_SERVER
    )
    logger.error(f"Failed to register MCP tools: {error_details.message}")
    raise


def create_server(config):
    """
    Create and configure the FastAPI server.

    Args:
        config: Application configuration

    Returns:
        Configured FastAPI application
    """
    # The initialization was moved to module level for simplicity
    # but could be refactored to be inside this function
    return app


if __name__ == "__main__":
    logger.info("Starting Google Ads MCP server...")
    # Check the application environment
    app_env = os.environ.get("APP_ENV", "dev")
    app_version = os.environ.get("APP_VERSION", "1.0.0")
    logger.info(f"Environment: {app_env}, Version: {app_version}")

    # Log health check initialization
    logger.info("Initializing health check service...")

    # Start the FastAPI application with the MCP server
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Server will be available at http://localhost:{port}")
    logger.info(f"Health check endpoint: http://localhost:{port}/health")
    logger.info(f"MCP server will be available at http://localhost:{port}/mcp")
    if os.environ.get("ENABLE_METRICS", "false").lower() == "true":
        logger.info(f"Metrics endpoint: http://localhost:{port}/metrics")
    uvicorn.run(app, host="0.0.0.0", port=port)
