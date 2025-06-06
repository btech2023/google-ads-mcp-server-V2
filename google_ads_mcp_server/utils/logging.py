"""
Logging Utility Module

This module provides logging configuration and utility functions for the Google Ads MCP Server,
including custom formatters, filters, and context-specific logging.
"""

import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import traceback

# Define default log levels
DEFAULT_CONSOLE_LEVEL = logging.INFO
DEFAULT_FILE_LEVEL = logging.DEBUG

# Define log format strings
DETAILED_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
SIMPLE_FORMAT = "[%(asctime)s] [%(levelname)s] - %(message)s"
JSON_FORMAT = {"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "line": "%(lineno)d", "message": "%(message)s"}

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON strings."""
    
    def __init__(self, fmt_dict: Dict[str, str] = None):
        """
        Initialize the JSON formatter.
        
        Args:
            fmt_dict: Format dictionary (keys will become JSON fields)
        """
        self.fmt_dict = fmt_dict or JSON_FORMAT
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_dict = {}

        # Ensure asctime is available for formatting
        if "asctime" not in record.__dict__:
            record.asctime = self.formatTime(record)
        # Ensure the message attribute exists for formatting
        if "message" not in record.__dict__:
            record.message = record.getMessage()
        
        # Apply the format dictionary
        for key, fmt in self.fmt_dict.items():
            value = fmt % record.__dict__
            if key == "line":
                try:
                    value = int(value)
                except ValueError:
                    pass
            log_dict[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_dict["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in ["args", "exc_info", "exc_text", "levelname", "levelno", 
                          "lineno", "module", "msecs", "msg", "name", "pathname", 
                          "process", "processName", "relativeCreated", "thread", 
                          "threadName", "asctime"] and not key.startswith("_"):
                log_dict[key] = value
        
        return json.dumps(log_dict)

class RequestContextFilter(logging.Filter):
    """Filter that adds request context information to log records."""
    
    def __init__(self, request_id_getter: callable = None):
        """
        Initialize the filter.
        
        Args:
            request_id_getter: Function that returns the current request ID
        """
        super().__init__()
        self.request_id_getter = request_id_getter or (lambda: None)
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to the log record."""
        record.request_id = self.request_id_getter()
        return True

def configure_logging(
    app_name: str = "google_ads_mcp_server", 
    console_level: int = DEFAULT_CONSOLE_LEVEL,
    file_level: int = DEFAULT_FILE_LEVEL,
    log_file_path: Optional[str] = None,
    json_output: bool = False,
    detailed_console: bool = True
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        app_name: Name of the application (used as logger name)
        console_level: Logging level for console output
        file_level: Logging level for file output
        log_file_path: Path to log file (if None, file logging is disabled)
        json_output: Whether to output logs in JSON format
        detailed_console: Whether to use detailed format for console output
        
    Returns:
        Configured logger
    """
    # Get the root logger
    logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Set the root logger level to the minimum of console and file levels
    logger.setLevel(min(console_level, file_level))

    # Ensure request context information is captured
    logger.addFilter(RequestContextFilter())
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    
    # Configure formatters based on settings
    if json_output:
        console_formatter = JsonFormatter()
    else:
        format_str = DETAILED_FORMAT if detailed_console else SIMPLE_FORMAT
        console_formatter = logging.Formatter(format_str)
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log file path is provided
    if log_file_path:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(file_level)
        
        if json_output:
            file_formatter = JsonFormatter()
        else:
            file_formatter = logging.Formatter(DETAILED_FORMAT)
        
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Create and return a named logger
    named_logger = logging.getLogger(app_name)
    named_logger.info(f"Logging configured for {app_name}")
    
    return named_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def add_request_context(request_id_getter: callable) -> None:
    """
    Add request context to all loggers.
    
    Args:
        request_id_getter: Function that returns the current request ID
    """
    root_logger = logging.getLogger()
    context_filter = RequestContextFilter(request_id_getter)
    root_logger.addFilter(context_filter)

def log_api_call(logger: logging.Logger, 
                service: str, 
                method: str, 
                customer_id: str, 
                params: Dict[str, Any],
                duration_ms: Optional[float] = None,
                success: bool = True,
                result_info: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an API call with standardized format.
    
    Args:
        logger: Logger to use
        service: Service name (e.g., 'CampaignService')
        method: Method name (e.g., 'get_campaigns')
        customer_id: Customer ID
        params: API call parameters
        duration_ms: Call duration in milliseconds (if available)
        success: Whether the call succeeded
        result_info: Additional information about the result
    """
    log_data = {
        "service": service,
        "method": method,
        "customer_id": customer_id,
        "params": params,
        "success": success
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    if result_info:
        log_data["result_info"] = result_info
    
    if success:
        logger.info(f"API call: {service}.{method}", extra={"api_call": log_data})
    else:
        logger.error(f"API call failed: {service}.{method}", extra={"api_call": log_data})

def log_mcp_request(logger: logging.Logger,
                   request_type: str,
                   request_id: str,
                   params: Dict[str, Any],
                   duration_ms: Optional[float] = None,
                   success: bool = True,
                   result_info: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an MCP request with standardized format.
    
    Args:
        logger: Logger to use
        request_type: Request type (e.g., 'tool', 'resource')
        request_id: Request ID
        params: Request parameters
        duration_ms: Request duration in milliseconds (if available)
        success: Whether the request succeeded
        result_info: Additional information about the result
    """
    log_data = {
        "request_type": request_type,
        "request_id": request_id,
        "params": params,
        "success": success
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = duration_ms
    
    if result_info:
        log_data["result_info"] = result_info
    
    if success:
        logger.info(f"MCP request: {request_type}", extra={"mcp_request": log_data})
    else:
        logger.error(f"MCP request failed: {request_type}", extra={"mcp_request": log_data})
