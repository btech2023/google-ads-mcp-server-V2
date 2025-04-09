# Google Ads MCP Server - Utility Integration Plan

This document outlines the plan for integrating the utility modules we've implemented into the existing Google Ads MCP Server codebase.

## 1. Utility Modules Summary

We have implemented the following utility modules:

1. **formatting.py** - Provides functions for formatting data (currency, dates, percentages, etc.)
2. **validation.py** - Provides input validation functions
3. **error_handler.py** - Provides standardized error handling and classification
4. **logging.py** - Provides logging configuration and utilities

## 2. Integration Strategy

Our integration strategy will follow these principles:

1. **Minimal disruption** - Replace existing similar functionality without breaking existing code
2. **Gradual adoption** - Introduce the utilities in phases, starting with critical components
3. **Consistent patterns** - Ensure all modules follow the same import and usage patterns

## 3. Integration Tasks

### 3.1. Replace Direct Formatting Logic

1. **Visualization Formatters** - Update the `visualization/formatters.py` module to use our utility functions.
   - Import the formatting utilities for currency, percentages, and dates.
   - Replace inline formatting logic with calls to our utility functions.

```python
# In visualization/formatters.py
from google_ads_mcp_server.utils.formatting import micros_to_currency, format_percentage, format_number, format_date
```

2. **Service Modules** - Find and replace formatting logic in various service modules:
   - Replace currency formatting in `google_ads/budgets.py`
   - Replace date formatting in all Google Ads service modules
   - Replace percentage formatting in reporting modules

### 3.2. Introduce Error Handling

1. **Google Ads Client** - Update the Google Ads client to use our error handler:
   - Import and use the error handler in `google_ads/client.py` and related modules
   - Replace existing error handling with standardized error handling

```python
# In google_ads/client.py
from google_ads_mcp_server.utils.error_handler import handle_exception, handle_google_ads_exception
```

2. **MCP Tools** - Add proper error handling to all MCP tool functions:
   - Wrap function execution in try/except blocks using our error handler
   - Return standardized error responses

3. **Server Code** - Update server error handling:
   - Use the error handler in FastAPI exception handlers
   - Apply consistent error response formats

### 3.3. Implement Validation

1. **Input Validation** - Add validation to all public endpoints:
   - Validate customer IDs
   - Validate date ranges
   - Validate numeric parameters

```python
# Example usage in mcp/tools/budget.py
from google_ads_mcp_server.utils.validation import validate_customer_id, validate_date_range
```

2. **Internal Validation** - Add validation to internal service functions:
   - Validate parameters before processing
   - Return early with appropriate errors for invalid inputs

### 3.4. Configure Logging

1. **Main Initialization** - Update main.py to use our logging configuration:
   - Replace existing logging setup with our configurable system
   - Configure log format based on environment

```python
# In main.py
from google_ads_mcp_server.utils.logging import configure_logging, add_request_context

# Replace existing logging setup with:
logger = configure_logging(
    app_name="google-ads-mcp",
    console_level=logging_level,
    log_file_path=config.get("log_file"),
    json_output=config.get("json_logs", False)
)
```

2. **Module Loggers** - Standardize logger usage across all modules:
   - Use the get_logger function to create module-specific loggers
   - Replace direct logging.getLogger calls

3. **Request Context** - Add request context to logs:
   - Implement the request context filter in the FastAPI middleware
   - Ensure all logs contain request IDs for traceability

## 4. Testing Plan

1. **Unit Tests** - Create unit tests for utility functions:
   - Test all formatting functions with various inputs
   - Test validation functions with valid and invalid inputs
   - Test error handler with different exception types

2. **Integration Tests** - Test the integrated modules:
   - Verify that the integrated components work correctly
   - Confirm that error handling is consistent across the application
   - Validate that logs contain the expected information

3. **Performance Testing** - Measure the impact on performance:
   - Compare response times before and after integration
   - Verify that caching still works effectively
   - Ensure no memory leaks or excessive resource usage

## 5. Implementation Timeline

1. **Phase 1 (Days 1-2)**: 
   - Add imports for utility modules in relevant files
   - Implement basic integration of formatting utilities
   - Add unit tests for utility functions

2. **Phase 2 (Days 3-4)**:
   - Integrate error handling utilities in critical components
   - Implement validation in public endpoints
   - Update logging configuration

3. **Phase 3 (Day 5)**:
   - Complete integration in all modules
   - Run full test suite
   - Document usage patterns for future reference

## 6. Backward Compatibility Considerations

1. **Function Signatures** - Ensure utility functions match existing patterns
2. **Error Responses** - Maintain consistent error response formats
3. **Logging Format** - Keep logging format similar to existing logs
4. **Performance** - Monitor for any performance regressions

## 7. Success Criteria

1. All utility functions are correctly integrated
2. Code maintainability is improved
3. Error handling is more consistent
4. Validation is more thorough
5. Logging provides better observability
6. No regressions in functionality or performance 