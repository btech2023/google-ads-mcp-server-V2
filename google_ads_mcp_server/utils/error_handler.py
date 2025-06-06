# -*- coding: utf-8 -*-
"""
Error Handler Utility Module

This module provides standardized error handling functions for the Google Ads MCP Server,
including error classification, formatting, and response generation.
"""

import logging
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Type, Union

from google.ads.googleads.errors import GoogleAdsException

logger = logging.getLogger(__name__)

# Error severity levels
SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_ERROR = "ERROR"
SEVERITY_CRITICAL = "CRITICAL"

# Error categories
CATEGORY_VALIDATION = "VALIDATION"
CATEGORY_AUTHENTICATION = "AUTHENTICATION"
CATEGORY_AUTHORIZATION = "AUTHORIZATION"
CATEGORY_API_ERROR = "API_ERROR"
CATEGORY_DATABASE = "DATABASE"
CATEGORY_CONFIG = "CONFIG"
CATEGORY_SERVER = "SERVER"
CATEGORY_NETWORK = "NETWORK"
CATEGORY_BUSINESS_LOGIC = "BUSINESS_LOGIC"


class ErrorDetails:
    """Class to store structured error information."""

    def __init__(
        self,
        message: str,
        error_type: str = None,
        severity: str = SEVERITY_ERROR,
        category: str = CATEGORY_SERVER,
        timestamp: datetime = None,
        exception: Exception = None,
        context: Dict[str, Any] = None,
    ):
        """
        Initialize error details.

        Args:
            message: Human-readable error message
            error_type: Type of error (e.g., class name of exception)
            severity: Error severity level
            category: Error category
            timestamp: When the error occurred
            exception: Original exception object
            context: Additional context information
        """
        self.message = message
        self.error_type = error_type or (
            exception.__class__.__name__ if exception else "UnknownError"
        )
        self.severity = severity
        self.category = category
        self.timestamp = timestamp or datetime.now()
        self.exception = exception
        self.context = context or {}
        self.traceback = traceback.format_exc() if exception else None

    def to_dict(self, include_traceback: bool = False) -> Dict[str, Any]:
        """
        Convert error details to a dictionary.

        Args:
            include_traceback: Whether to include the traceback in the output

        Returns:
            Dictionary representation of error details
        """
        result = {
            "message": self.message,
            "error_type": self.error_type,
            "severity": self.severity,
            "category": self.category,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
        }

        if include_traceback and self.traceback:
            result["traceback"] = self.traceback

        return result

    def log(self):
        """Log the error with appropriate severity level."""
        log_message = f"{self.error_type}: {self.message}"

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            log_message += f" [Context: {context_str}]"

        if self.severity == SEVERITY_CRITICAL:
            logger.critical(log_message, exc_info=self.exception)
        elif self.severity == SEVERITY_ERROR:
            logger.error(log_message, exc_info=self.exception)
        elif self.severity == SEVERITY_WARNING:
            logger.warning(log_message, exc_info=self.exception)
        else:
            logger.info(log_message)


def handle_exception(
    exception: Exception,
    context: Dict[str, Any] = None,
    severity: str = None,
    category: str = None,
) -> ErrorDetails:
    """
    Handle an exception by creating error details and logging it.

    Args:
        exception: The exception to handle
        context: Additional context information
        severity: Override default severity level
        category: Override default error category

    Returns:
        ErrorDetails object
    """
    # Default classifications based on exception type
    error_details = classify_exception(exception, context)

    # Override severity and category if provided
    if severity:
        error_details.severity = severity
    if category:
        error_details.category = category

    # Log the error
    error_details.log()

    return error_details


def classify_exception(
    exception: Exception, context: Dict[str, Any] = None
) -> ErrorDetails:
    """
    Classify an exception into appropriate severity and category.

    Args:
        exception: The exception to classify
        context: Additional context information

    Returns:
        ErrorDetails object
    """
    context = context or {}

    # Handle Google Ads API exceptions
    if isinstance(exception, GoogleAdsException):
        return handle_google_ads_exception(exception, context)

    # Handle common exception types
    if isinstance(exception, (ValueError, TypeError, KeyError, IndexError)):
        message = str(exception) or "Validation error"
        return ErrorDetails(
            message=message,
            exception=exception,
            severity=SEVERITY_WARNING,
            category=CATEGORY_VALIDATION,
            context=context,
        )

    if isinstance(exception, (PermissionError, OSError)):
        message = str(exception) or "System error"
        return ErrorDetails(
            message=message,
            exception=exception,
            severity=SEVERITY_ERROR,
            category=CATEGORY_SERVER,
            context=context,
        )

    # Default handling for other exceptions
    message = str(exception) or "An unexpected error occurred"
    return ErrorDetails(
        message=message,
        exception=exception,
        severity=SEVERITY_ERROR,
        category=CATEGORY_SERVER,
        context=context,
    )


def handle_google_ads_exception(
    exception: GoogleAdsException, context: Dict[str, Any] = None
) -> ErrorDetails:
    """
    Handle Google Ads API exceptions.

    Args:
        exception: The GoogleAdsException
        context: Additional context information

    Returns:
        ErrorDetails object
    """
    context = context or {}

    # Extract details from the exception
    errors = []
    failure = exception.failure
    if failure:
        for error in failure.errors:
            errors.append(
                {
                    "error_code": error.error_code.enum_name,
                    "message": error.message,
                    "location": {
                        "field_path": (
                            error.location.field_path_elements
                            if hasattr(error.location, "field_path_elements")
                            else None
                        )
                    },
                }
            )

    # Add errors to context
    context["google_ads_errors"] = errors

    # Determine appropriate category and severity
    category = CATEGORY_API_ERROR
    severity = SEVERITY_ERROR

    # Check for authentication/authorization errors
    auth_error_codes = [
        "AUTHENTICATION_ERROR",
        "AUTHORIZATION_ERROR",
        "CUSTOMER_NOT_FOUND",
        "TOKEN_ERROR",
    ]
    for error in errors:
        if error.get("error_code") in auth_error_codes:
            category = CATEGORY_AUTHENTICATION
            severity = SEVERITY_CRITICAL
            break

    # Create the error message
    if errors:
        # Use the first error message as the main message
        message = errors[0].get("message", str(exception))
        if len(errors) > 1:
            message += f" (and {len(errors)-1} more errors)"
    else:
        message = str(exception) or "Google Ads API error"

    return ErrorDetails(
        message=message,
        exception=exception,
        severity=severity,
        category=category,
        context=context,
    )


def create_error_response(
    error_details: ErrorDetails, include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.

    Args:
        error_details: Error details object
        include_traceback: Whether to include the traceback in the response

    Returns:
        Error response dictionary
    """
    response = {
        "type": "error",
        "error": error_details.to_dict(include_traceback=include_traceback),
    }

    return response


def handle_and_respond(
    func, *args, include_traceback: bool = False, **kwargs
) -> Tuple[bool, Union[Dict[str, Any], Any]]:
    """
    Execute a function with exception handling and return a standardized response.

    Args:
        func: Function to execute
        include_traceback: Whether to include traceback in error responses
        *args, **kwargs: Arguments to pass to the function

    Returns:
        Tuple of (success, result_or_error_response)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        error_details = handle_exception(e, context={"args": args, "kwargs": kwargs})
        error_response = create_error_response(
            error_details, include_traceback=include_traceback
        )
        return False, error_response
