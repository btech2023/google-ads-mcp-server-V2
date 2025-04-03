#!/usr/bin/env python
"""
Google Ads MCP Server - Main Entry Point

This module serves as the entry point for the Google Ads MCP Server application.
"""

import os
import logging
from config import config
from server import create_server
from health import setup_health_checks
from mcp.handlers import register_mcp_handlers
import uvicorn

def main():
    # Setup logging
    logging_level = getattr(logging, config.get("log_level", "INFO"))
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("google-ads-mcp")
    logger.info("Starting Google Ads MCP server...")
    
    # Log app version and environment
    app_env = config.env.value
    app_version = config.get("version", "1.0.0")
    logger.info(f"Environment: {app_env}, Version: {app_version}")
    
    # Create server
    app = create_server(config)
    
    # Register MCP handlers
    register_mcp_handlers(app)
    
    # Setup health checks
    logger.info("Initializing health check service...")
    setup_health_checks(app)
    
    # Start the server
    host = config.get("api_host", "0.0.0.0")
    port = config.get("api_port", 8000)
    logger.info(f"Server will be available at http://{host}:{port}")
    logger.info(f"Health check endpoint: http://{host}:{port}/health")
    logger.info(f"MCP server will be available at http://{host}:{port}/mcp")
    
    if config.get("enable_metrics", False):
        logger.info(f"Metrics endpoint: http://{host}:{port}/metrics")
    
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()
