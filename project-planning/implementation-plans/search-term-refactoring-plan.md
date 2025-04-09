# Detailed Refactoring Plan for search_term.py

## 1. Overview and Analysis

`search_term.py` contains four key MCP tools:
1. `get_search_terms_report`: Retrieve search terms with optional filtering
2. `get_search_terms_report_json`: Get search terms in JSON format for visualization
3. `analyze_search_terms`: Generate insights about search term performance
4. `analyze_search_terms_json`: Provides search term analysis in JSON format for visualization

The module currently has the following issues:
- Uses standard logging instead of `utils.logging.get_logger`
- Lacks proper validation for parameters like customer_id, dates, etc.
- Contains manual customer ID formatting
- Uses simple error strings/dictionaries instead of standardized error responses
- Contains duplicated code for validation
- Has inconsistent error handling without contextual information

## 2. Refactoring Steps

### 2.1 Initial Setup (15 min)

1. Add required imports:
```python
from utils.logging import get_logger
from utils.validation import (
    validate_customer_id, 
    validate_date_format,
    validate_string_length
)
from utils.error_handler import (
    create_error_response, 
    handle_exception,
    CATEGORY_VALIDATION,
    SEVERITY_ERROR
)
from utils.formatting import format_customer_id
```

2. Replace standard logger with utils-provided logger:
```python
logger = get_logger(__name__)
```

### 2.2 Method Refactoring

#### 2.2.1 `get_search_terms_report` (45 min)

**Validation Requirements:**
- `customer_id`: Must be a valid Google Ads customer ID
- `campaign_id` and `ad_group_id`: If provided, must be non-empty strings
- `start_date` and `end_date`: If provided, must be valid YYYY-MM-DD format and start_date ≤ end_date

**Implementation Plan:**
1. Add input validation at the beginning of the method:
```python
# Validate inputs
input_errors = []

if not validate_customer_id(customer_id):
    input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
    
if campaign_id and not validate_string_length(campaign_id, min_length=1):
    input_errors.append(f"Invalid campaign_id: {campaign_id}.")
    
if ad_group_id and not validate_string_length(ad_group_id, min_length=1):
    input_errors.append(f"Invalid ad_group_id: {ad_group_id}.")
    
if start_date and not validate_date_format(start_date):
    input_errors.append(f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD.")
    
if end_date and not validate_date_format(end_date):
    input_errors.append(f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD.")
    
# Check date order
if start_date and end_date:
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    if start_dt > end_dt:
        input_errors.append(f"start_date ({start_date}) must be before end_date ({end_date}).")
        
# Return error if validation failed
if input_errors:
    error_msg = "; ".join(input_errors)
    logger.warning(f"Validation error in get_search_terms_report: {error_msg}")
    return create_error_response(handle_exception(
        ValueError(error_msg), 
        category=CATEGORY_VALIDATION,
        context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
    ))
```

2. Replace customer ID handling:
```python
# Remove dashes from customer ID if present
clean_customer_id = customer_id.replace('-', '')
```

3. Update service call with clean_customer_id:
```python
search_terms = await search_term_service.get_search_terms(
    customer_id=clean_customer_id,
    campaign_id=campaign_id,
    ad_group_id=ad_group_id,
    start_date=start_date,
    end_date=end_date
)
```

4. Standardize error handling for empty results:
```python
if not search_terms:
    return create_error_response(handle_exception(
        ValueError("No search terms found with the specified filters."),
        category=CATEGORY_VALIDATION,
        context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id}
    ))
```

5. Use format_customer_id for display:
```python
# Format with dashes for display
display_customer_id = format_customer_id(clean_customer_id)
```

6. Update exception handling:
```python
except Exception as e:
    error_details = handle_exception(
        e,
        context={"customer_id": customer_id, "campaign_id": campaign_id, "ad_group_id": ad_group_id, "start_date": start_date, "end_date": end_date}
    )
    logger.error(f"Error getting search terms report: {str(e)}")
    return create_error_response(error_details)
```

#### 2.2.2 `get_search_terms_report_json` (30 min)

**Validation Requirements:**
- Identical to `get_search_terms_report`

**Implementation Plan:**
- Apply the same validation and error handling patterns as in `get_search_terms_report`
- Modify the error responses to use the standardized format

#### 2.2.3 `analyze_search_terms` (45 min)

**Validation Requirements:**
- Identical to `get_search_terms_report`

**Implementation Plan:**
- Apply the same validation and error handling patterns as in `get_search_terms_report`
- Additional attention to returning proper error responses for analysis-specific logic

#### 2.2.4 `analyze_search_terms_json` (30 min)

**Validation Requirements:**
- Identical to `analyze_search_terms`

**Implementation Plan:**
- Apply the same validation and error handling patterns as in `analyze_search_terms`
- Format error responses in JSON format using standardized structure

### 2.3 Testing (30 min)

1. Test all methods with:
   - Valid inputs to ensure normal operation
   - Invalid customer IDs to check validation
   - Invalid campaign_id, ad_group_id to check ID validation
   - Invalid date formats to check date validation
   - End date before start date to check date order validation
   - Proper error handling in all cases

## 3. Implementation Timeline

**Total estimated time: 3 hours**

- Initial setup (imports, logger): 15 minutes
- Refactoring get_search_terms_report: 45 minutes
- Refactoring get_search_terms_report_json: 30 minutes
- Refactoring analyze_search_terms: 45 minutes
- Refactoring analyze_search_terms_json: 30 minutes
- Testing: 30 minutes

## 4. Expected Outcome

A fully refactored `search_term.py` module with:
- Proper validation of all input parameters
- Standardized error handling with helpful, contextual error messages
- Consistent use of utility functions for validation, logging, error handling, and formatting
- Improved error context to aid in debugging
- Reduced code duplication through use of utility modules

## 5. Implementation Progress Tracking

- [ ] Added required imports from utility modules
- [ ] Replaced standard logger with get_logger
- [ ] Refactored get_search_terms_report with validation and error handling
- [ ] Refactored get_search_terms_report_json with validation and error handling
- [ ] Refactored analyze_search_terms with validation and error handling
- [ ] Refactored analyze_search_terms_json with validation and error handling
- [ ] Tested with various valid and invalid inputs
- [ ] Updated implementation plan to mark search_term.py as complete 