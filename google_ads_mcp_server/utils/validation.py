"""
Validation Utility Module

This module provides input validation functions for the Google Ads MCP
Server to ensure data integrity, parameter correctness, and API
compliance.
"""

import logging
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


def validate_not_empty_string(value: str, param_name: str = "") -> bool:
    """Validate that ``value`` is a non-empty string.

    Args:
        value: The string to validate.
        param_name: Optional name of the parameter for logging context.

    Returns:
        ``True`` if ``value`` is a string and not empty after stripping
        whitespace, otherwise ``False``.
    """
    if value is None or not isinstance(value, str) or not value.strip():
        if param_name:
            logger.warning("%s is empty", param_name)
        else:
            logger.warning("String value is empty")
        return False
    return True


def validate_non_empty_string(
    value: Any, param_name: str, errors: List[str]
) -> bool:
    """Validate that ``value`` is a non-empty string and collect errors.

    Args:
        value: The value to validate.
        param_name: Name of the parameter being validated.
        errors: List for collecting validation error messages.

    Returns:
        ``True`` if ``value`` is a non-empty string, otherwise ``False``.
    """
    if not isinstance(value, str) or not value.strip():
        message = f"{param_name} must be a non-empty string"
        logger.warning(message)
        errors.append(message)
        return False

    return True


def validate_not_none(value: Any, param_name: str = "") -> bool:
    """Return ``True`` if ``value`` is not ``None``."""
    if value is None:
        if param_name:
            logger.warning("%s is None", param_name)
        else:
            logger.warning("Value is None")
        return False
    return True


def _validate_id(value: Union[int, str], name: str) -> bool:
    if value is None:
        return False
    if isinstance(value, int):
        return value > 0
    if isinstance(value, str):
        if not value.isdigit():
            logger.warning("%s '%s' is not numeric", name, value)
            return False
        return int(value) > 0
    logger.warning("%s '%s' is not a string or integer", name, value)
    return False


def validate_campaign_id(campaign_id: Union[int, str]) -> bool:
    """Validate that a campaign ID represents a positive integer."""
    return _validate_id(campaign_id, "campaign_id")


def validate_ad_group_id(ad_group_id: Union[int, str]) -> bool:
    """Validate that an ad group ID represents a positive integer."""
    return _validate_id(ad_group_id, "ad_group_id")


def validate_keyword_id(keyword_id: Union[int, str]) -> bool:
    """Validate that a keyword ID represents a positive integer."""
    return _validate_id(keyword_id, "keyword_id")


def validate_date_range_string(date_range: str) -> bool:
    """Validate that a date range string is one of the supported constants."""
    if not isinstance(date_range, str):
        return False
    valid_ranges = {
        "LAST_7_DAYS",
        "LAST_14_DAYS",
        "LAST_30_DAYS",
        "LAST_90_DAYS",
        "THIS_MONTH",
        "LAST_MONTH",
        "PREVIOUS_7_DAYS",
        "PREVIOUS_14_DAYS",
        "PREVIOUS_30_DAYS",
        "PREVIOUS_90_DAYS",
        "PREVIOUS_MONTH",
        "PREVIOUS_YEAR",
    }
    if date_range not in valid_ranges:
        logger.warning("Invalid date range: %s", date_range)
        return False
    return True


def validate_customer_id(customer_id: str) -> bool:
    """
    Validate that a customer ID is in the correct format.

    Args:
        customer_id: The customer ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not customer_id:
        logger.warning("Customer ID is empty")
        return False

    # Remove any dashes
    clean_id = customer_id.replace("-", "")

    # Check if it's 10 digits
    if not clean_id.isdigit() or len(clean_id) != 10:
        logger.warning(f"Invalid customer ID format: {customer_id}")
        return False

    return True


def validate_date_format(date_str: str) -> bool:
    """
    Validate that a date string is in YYYY-MM-DD format.

    Args:
        date_str: The date string to validate

    Returns:
        True if valid, False otherwise
    """
    if not date_str:
        return False

    # Check format
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if not date_pattern.match(date_str):
        logger.warning(f"Invalid date format: {date_str}, expected YYYY-MM-DD")
        return False

    # Check if it's a valid date
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        logger.warning(f"Invalid date: {date_str}")
        return False


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate that a date range is valid.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        True if valid, False otherwise
    """
    # Validate each date format
    if (
        not validate_date_format(start_date)
        or not validate_date_format(end_date)
    ):
        return False

    # Check if start_date is before end_date
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    if start > end:
        logger.warning(
            "Invalid date range: start_date %s is after end_date %s",
            start_date,
            end_date,
        )
        return False

    return True


def validate_enum(
    value: str, valid_values: List[str], case_sensitive: bool = False
) -> bool:
    """
    Validate that a value is one of a list of valid values.

    Args:
        value: The value to validate
        valid_values: List of valid values
        case_sensitive: Whether the comparison should be case-sensitive

    Returns:
        True if valid, False otherwise
    """
    if value is None:
        return False

    if not case_sensitive:
        value = value.upper()
        valid_values = [v.upper() for v in valid_values]

    if value not in valid_values:
        logger.warning(
            "Invalid value: %s, expected one of: %s",
            value,
            ", ".join(valid_values),
        )
        return False

    return True


def validate_numeric_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
) -> bool:
    """
    Validate that a numeric value is within a specified range.

    Args:
        value: The value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)

    Returns:
        True if valid, False otherwise
    """
    if value is None:
        return False

    if min_value is not None and value < min_value:
        logger.warning(f"Value {value} is less than minimum {min_value}")
        return False

    if max_value is not None and value > max_value:
        logger.warning(f"Value {value} is greater than maximum {max_value}")
        return False

    return True


def validate_float_range(
    value: Any,
    min_value: float,
    max_value: float,
) -> bool:
    """Validate that a float is within a given range."""
    if value is None or not isinstance(value, (int, float)):
        return False

    value = float(value)

    if value < min_value or value > max_value:
        logger.warning(
            "Value %s out of range %.2f - %.2f", value, min_value, max_value
        )
        return False

    return True


def validate_positive_integer(value: Any) -> bool:
    """Validate that ``value`` is a positive integer.

    Args:
        value: The value to validate.

    Returns:
        ``True`` if ``value`` is an ``int`` greater than ``0``.
    """
    if value is None:
        return False

    if not isinstance(value, int):
        logger.warning("Value %s is not an integer", value)
        return False

    if value <= 0:
        logger.warning("Value %s is not positive", value)
        return False

    return True


def validate_string_length(
    text: str, min_length: int = 0, max_length: Optional[int] = None
) -> bool:
    """
    Validate that a string length is within specified bounds.

    Args:
        text: The string to validate
        min_length: Minimum allowed length (inclusive)
        max_length: Maximum allowed length (inclusive)

    Returns:
        True if valid, False otherwise
    """
    if text is None:
        return False

    if len(text) < min_length:
        logger.warning(
            "String length %s is less than minimum %s",
            len(text),
            min_length,
        )
        return False

    if max_length is not None and len(text) > max_length:
        logger.warning(
            "String length %s is greater than maximum %s",
            len(text),
            max_length,
        )
        return False

    return True


def validate_regex(text: str, pattern: str) -> bool:
    """
    Validate that a string matches a regex pattern.

    Args:
        text: The string to validate
        pattern: Regular expression pattern

    Returns:
        True if valid, False otherwise
    """
    if text is None:
        return False

    regex = re.compile(pattern)
    if not regex.match(text):
        logger.warning(f"String '{text}' does not match pattern '{pattern}'")
        return False

    return True


def validate_all(validations: List[Tuple[Callable, List, Dict]]) -> bool:
    """
    Run multiple validation functions and return True only if all pass.

    Args:
        validations: List of tuples (validation_function, args, kwargs)

    Returns:
        True if all validations pass, False otherwise
    """
    for validation_func, args, kwargs in validations:
        if not validation_func(*args, **kwargs):
            return False

    return True


def validate_any(validations: List[Tuple[Callable, List, Dict]]) -> bool:
    """
    Run multiple validation functions and return True if any pass.

    Args:
        validations: List of tuples (validation_function, args, kwargs)

    Returns:
        True if any validation passes, False otherwise
    """
    for validation_func, args, kwargs in validations:
        if validation_func(*args, **kwargs):
            return True

    return False


def sanitize_input(
    value: str,
    max_length: Optional[int] = None,
    allowed_chars: Optional[str] = None,
) -> str:
    """
    Sanitize input string by applying length limits and character restrictions.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        allowed_chars: Regex pattern of allowed characters

    Returns:
        Sanitized string
    """
    if value is None:
        return ""

    # Apply length limit
    if max_length is not None and len(value) > max_length:
        value = value[:max_length]

    # Apply character restrictions
    if allowed_chars is not None:
        regex = re.compile(f"[^{re.escape(allowed_chars)}]")
        value = regex.sub("", value)

    return value


def validate_budget_id(budget_id: Union[int, str]) -> bool:
    """Validate that a campaign budget ID is a positive integer.

    Args:
        budget_id: The budget ID to validate. Can be an ``int`` or a ``str`` of
            digits.

    Returns:
        ``True`` if ``budget_id`` represents a positive integer, otherwise
        ``False``.
    """
    if budget_id is None:
        return False

    if isinstance(budget_id, int):
        return budget_id > 0

    if isinstance(budget_id, str):
        if not budget_id.isdigit():
            logger.warning("Budget ID '%s' is not numeric", budget_id)
            return False
        return int(budget_id) > 0

    logger.warning("Budget ID '%s' is not a string or integer", budget_id)
    return False


def validate_list(
    value: Any,
    param_name: str,
    errors: List[str],
    *,
    allow_empty: bool = False,
) -> bool:
    """Validate that ``value`` is a list.

    Args:
        value: The value to validate.
        param_name: Parameter name for error messages.
        errors: List for collecting validation error messages.
        allow_empty: Whether an empty list is considered valid.

    Returns:
        ``True`` if validation passes, otherwise ``False``.
    """
    if not isinstance(value, list):
        message = f"{param_name} must be a list"
        logger.warning(message)
        errors.append(message)
        return False

    if not value and not allow_empty:
        message = f"{param_name} must not be empty"
        logger.warning(message)
        errors.append(message)
        return False

    return True


def validate_dict(
    value: Any,
    param_name: str,
    errors: List[str],
    *,
    allow_empty: bool = False,
) -> bool:
    """Validate that ``value`` is a dictionary."""
    if not isinstance(value, dict):
        message = f"{param_name} must be a dict"
        logger.warning(message)
        errors.append(message)
        return False

    if not value and not allow_empty:
        message = f"{param_name} must not be empty"
        logger.warning(message)
        errors.append(message)
        return False

    return True


def validate_list_not_empty(value: Any) -> bool:
    """Return ``True`` if ``value`` is a non-empty list."""
    return isinstance(value, list) and len(value) > 0


def validate_list_of_strings(
    value: Any, *, allow_empty: bool = False
) -> bool:
    """Validate that ``value`` is a list of strings."""
    if not isinstance(value, list):
        return False

    if not value and not allow_empty:
        return False

    return all(isinstance(item, str) for item in value)


def validate_list_of_dicts(
    value: Any,
    *,
    required_keys: Optional[List[str]] = None,
    allow_empty: bool = False,
) -> bool:
    """Validate that ``value`` is a list of dictionaries."""
    if not isinstance(value, list):
        return False

    if not value and not allow_empty:
        return False

    required_keys = required_keys or []
    for item in value:
        if not isinstance(item, dict):
            return False
        for key in required_keys:
            if key not in item:
                return False

    return True


def validate_dict_keys(value: Any, required_keys: List[str]) -> bool:
    """Validate that a dictionary contains the required keys."""
    if not isinstance(value, dict):
        return False

    for key in required_keys:
        if key not in value:
            return False

    return True


def validate_non_negative_number(
    value: Any, param_name: str, errors: List[str]
) -> bool:
    """Validate that a number is non-negative."""
    if not isinstance(value, (int, float)) or value < 0:
        message = f"{param_name} must be a non-negative number"
        logger.warning(message)
        errors.append(message)
        return False

    return True
