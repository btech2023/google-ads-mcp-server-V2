# Google Ads MCP Server - Utility Modules

This directory contains utility modules that provide common functionality used throughout the Google Ads MCP Server.

## Modules

### `formatting.py`

Provides functions for formatting data in various ways:

- **Customer ID Formatting**: Format and clean Google Ads customer IDs
- **Currency Formatting**: Convert between micros (millionths) and formatted currency strings
- **Date Formatting**: Format dates consistently across the application
- **Percentage Formatting**: Format values as percentages
- **Number Formatting**: Format numbers with thousands separators
- **String Truncation**: Truncate strings to a maximum length

```python
from google_ads_mcp_server.utils.formatting import format_customer_id, micros_to_currency

# Format a customer ID: "1234567890" -> "123-456-7890"
formatted_id = format_customer_id("1234567890")

# Format currency: 1234567 -> "$1.23"
formatted_currency = micros_to_currency(1234567)
```

### `validation.py`

Provides functions for validating input data:

- **Customer ID Validation**: Validate Google Ads customer IDs
- **Date Validation**: Validate date formats and date ranges
- **Enum Validation**: Validate values against a list of valid values
- **Range Validation**: Validate numeric values within a range
- **String Validation**: Validate string length and pattern matching
- **Composite Validation**: Validate with multiple conditions (validate_all, validate_any)
- **Input Sanitization**: Clean and sanitize user input

```python
from google_ads_mcp_server.utils.validation import validate_customer_id, validate_date_range

# Validate a customer ID
is_valid = validate_customer_id("123-456-7890")  # True

# Validate a date range
is_valid = validate_date_range("2023-01-01", "2023-01-31")  # True
```

### `error_handler.py`

Provides standardized error handling and formatting:

- **Error Classification**: Categorize exceptions by type and severity
- **Google Ads API Error Handling**: Special handling for Google Ads API errors
- **Standardized Error Responses**: Create consistent error response structures
- **Error Context**: Add context information to error details
- **Logging Integration**: Automatically log errors with appropriate severity

```python
from google_ads_mcp_server.utils.error_handler import handle_exception, create_error_response

try:
    # Some code that might raise an exception
    result = process_data()
except Exception as e:
    # Handle the exception
    error_details = handle_exception(e, context={"customer_id": "123-456-7890"})
    
    # Create a standardized error response
    error_response = create_error_response(error_details)
    return error_response
```

### `logging.py`

Provides logging configuration and utilities:

- **Logging Configuration**: Configure logging consistently across the application
- **JSON Formatting**: Format logs as JSON for easier parsing
- **Request Context**: Add request context (like request ID) to all logs
- **Specialized Logging**: Log API calls and MCP requests with standardized formats
- **Log Level Management**: Configure log levels based on environment

```python
from google_ads_mcp_server.utils.logging import configure_logging, log_api_call

# Configure logging for the application
logger = configure_logging(
    app_name="google-ads-mcp",
    console_level=logging.INFO,
    log_file_path="logs/app.log"
)

# Log an API call
log_api_call(
    logger,
    service="CampaignService",
    method="get_campaigns",
    customer_id="123-456-7890",
    params={"start_date": "2023-01-01", "end_date": "2023-01-31"},
    duration_ms=123,
    success=True
)
```

## Usage Guidelines

1. **Import Consistency**: Always import from the full module path (`google_ads_mcp_server.utils.xxx`)
2. **Error Handling**: Use `error_handler.py` for all exception handling
3. **Validation**: Validate all inputs using `validation.py` functions
4. **Formatting**: Use `formatting.py` for all data formatting needs
5. **Logging**: Configure logging with `logging.py` and use its specialized functions

## Testing

Each utility module has corresponding unit tests in the `tests/unit/` directory:

- `test_formatting.py`
- `test_validation.py`
- `test_error_handler.py`
- `test_logging.py`

To run all utility tests:

```bash
python -m google_ads_mcp_server.tests.unit.run_utility_tests
``` 