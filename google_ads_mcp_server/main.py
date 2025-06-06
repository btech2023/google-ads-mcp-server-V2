#!/usr/bin/env python
"""
Google Ads MCP Server - Main Entry Point

This module serves as the entry point for the Google Ads MCP Server application.
"""

import logging
from .config import config
from .server import create_server
from .health import setup_health_checks
from .mcp.handlers import register_mcp_handlers
import uvicorn

# Import logging utilities
from google_ads_mcp_server.utils.logging import (
    configure_logging,
    add_request_context
)

def main():
    # Setup logging with our utility
    logging_level = getattr(logging, config.get("log_level", "INFO"))
    log_file_path = config.get("log_file_path")
    json_logs = config.get("json_logs", False)
    
    # Configure logging
    logger = configure_logging(
        app_name="google-ads-mcp",
        console_level=logging_level,
        file_level=logging.DEBUG if log_file_path else None,
        log_file_path=log_file_path,
        json_output=json_logs,
        detailed_console=True
    )
    
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
    
    # Add request context to logging
    def get_request_id():
        # This will be populated by middleware in server.py
        # We're just defining the function here, to be used later
        pass
    
    add_request_context(get_request_id)
    
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
