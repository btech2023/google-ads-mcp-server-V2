# Detailed Refactoring Plan for budget.py

## 1. Overview and Analysis

`budget.py` contains four key MCP tools:
1. `get_budgets`: Retrieve campaign budgets with optional filtering
2. `get_budgets_json`: Get campaign budgets in JSON format for visualization
3. `analyze_budgets`: Generate insights about budget performance
4. `update_budget`: Update budget properties (amount, name, delivery method)

The module currently has the following issues:
- Uses standard logging instead of `utils.logging.get_logger`
- Lacks proper validation for parameters like customer_id, budget_ids, days_to_analyze, etc.
- Contains manual customer ID formatting
- Uses simple error strings/dictionaries instead of standardized error responses
- Has inconsistent error handling without contextual information
- Budget-specific validation is needed for parameters like amount (ensure positive values)

## 2. Refactoring Steps

### 2.1 Initial Setup (15 min)

1. Add required imports:
```python
from utils.logging import get_logger
from utils.validation import (
    validate_customer_id, 
    validate_string_length,
    validate_numeric_range,
    validate_enum
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

#### 2.2.1 `get_budgets` (45 min)

**Validation Requirements:**
- `customer_id`: Must be a valid Google Ads customer ID
- `status`: If provided, must be a valid budget status value
- `budget_ids`: If provided, validate it's a non-empty string

**Implementation Plan:**
1. Add input validation at the beginning of the method:
```python
# Validate inputs
input_errors = []

if not validate_customer_id(customer_id):
    input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
    
if status and not validate_enum(status, ["ENABLED", "REMOVED", "UNKNOWN"], case_sensitive=False):
    input_errors.append(f"Invalid status: {status}. Expected one of: ENABLED, REMOVED, UNKNOWN.")
    
if budget_ids and not validate_string_length(budget_ids, min_length=1):
    input_errors.append(f"Invalid budget_ids: {budget_ids}. Must be a non-empty string.")
    
# Return error if validation failed
if input_errors:
    error_msg = "; ".join(input_errors)
    logger.warning(f"Validation error in get_budgets: {error_msg}")
    return create_error_response(handle_exception(
        ValueError(error_msg), 
        category=CATEGORY_VALIDATION,
        context={"customer_id": customer_id, "status": status, "budget_ids": budget_ids}
    ))
```

2. Replace customer ID handling:
```python
# Remove dashes from customer ID if present
clean_customer_id = customer_id.replace('-', '')
```

3. Update service call with clean_customer_id:
```python
budgets = await budget_service.get_budgets(
    customer_id=clean_customer_id,
    status_filter=status,
    budget_ids=budget_id_list
)
```

4. Standardize error handling for empty results:
```python
if not budgets:
    return create_error_response(handle_exception(
        ValueError("No campaign budgets found with the specified filters."),
        category=CATEGORY_VALIDATION,
        context={"customer_id": customer_id, "status": status, "budget_ids": budget_ids}
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
        context={"customer_id": customer_id, "status": status, "budget_ids": budget_ids}
    )
    logger.error(f"Error getting campaign budgets: {str(e)}")
    return create_error_response(error_details)
```

#### 2.2.2 `get_budgets_json` (30 min)

**Validation Requirements:**
- Identical to `get_budgets`

**Implementation Plan:**
- Apply the same validation and error handling patterns as in `get_budgets`
- Modify the error responses to use the standardized format

#### 2.2.3 `analyze_budgets` (45 min)

**Validation Requirements:**
- `customer_id`: Must be a valid Google Ads customer ID
- `budget_ids`: If provided, validate it's a non-empty string
- `days_to_analyze`: Must be a positive integer

**Implementation Plan:**
1. Add validation for days_to_analyze:
```python
if not validate_numeric_range(days_to_analyze, min_value=1, max_value=365):
    input_errors.append(f"Invalid days_to_analyze: {days_to_analyze}. Must be between 1 and 365.")
```

2. Apply the same validation and error handling patterns as in `get_budgets`
3. Additional attention to returning proper error responses for analysis-specific logic

#### 2.2.4 `update_budget` (45 min)

**Validation Requirements:**
- `customer_id`: Must be a valid Google Ads customer ID
- `budget_id`: Must be a non-empty string
- `amount`: If provided, must be a positive number
- `name`: If provided, must be a non-empty string
- `delivery_method`: If provided, must be a valid value ("STANDARD" or "ACCELERATED")
- At least one of amount, name, or delivery_method must be provided

**Implementation Plan:**
1. Add budget-specific validation:
```python
# Validate inputs
input_errors = []

if not validate_customer_id(customer_id):
    input_errors.append(f"Invalid customer_id format: {customer_id}. Expected 10 digits.")
    
if not validate_string_length(budget_id, min_length=1):
    input_errors.append(f"Budget ID is required.")
    
if amount is not None and not validate_numeric_range(amount, min_value=0):
    input_errors.append(f"Invalid amount: {amount}. Must be a positive number.")
    
if name is not None and not validate_string_length(name, min_length=1):
    input_errors.append(f"Invalid name: {name}. Must be a non-empty string.")
    
if delivery_method is not None and not validate_enum(delivery_method, ["STANDARD", "ACCELERATED"], case_sensitive=True):
    input_errors.append(f"Invalid delivery_method: {delivery_method}. Must be one of: STANDARD, ACCELERATED.")
    
# Ensure at least one field to update is provided
if amount is None and name is None and delivery_method is None:
    input_errors.append("At least one of amount, name, or delivery_method must be provided.")
```

2. Apply the same validation and error handling patterns as in the other methods
3. Special handling for the conversion of amount to micros:
```python
# Convert amount to micros if provided
amount_micros = None
if amount is not None:
    amount_micros = int(amount * 1000000)  # Convert to micros
```

4. Properly handle error responses from the budget service:
```python
if not result.get("success", False):
    return create_error_response(handle_exception(
        ValueError(result.get('error', 'Unknown error')),
        category=CATEGORY_VALIDATION,
        context={"customer_id": customer_id, "budget_id": budget_id}
    ))
```

### 2.3 Testing (30 min)

1. Test all methods with:
   - Valid inputs to ensure normal operation
   - Invalid customer IDs to check validation
   - Invalid budget_ids to check validation
   - Invalid status values to check enum validation
   - Invalid amounts (negative values) to check numeric validation
   - Missing required fields to check validation logic
   - Proper error handling in all cases

## 3. Implementation Timeline

**Total estimated time: 3.5 hours**

- Initial setup (imports, logger): 15 minutes
- Refactoring get_budgets: 45 minutes
- Refactoring get_budgets_json: 30 minutes
- Refactoring analyze_budgets: 45 minutes
- Refactoring update_budget: 45 minutes
- Testing: 30 minutes

## 4. Budget-Specific Considerations

1. **Amount Validation**:
   - Budget amounts must be positive
   - Proper conversion between dollars and micros (1 dollar = 1,000,000 micros)
   - Handle floating-point precision issues when converting to micros

2. **Budget Service Error Handling**:
   - The budget service already returns structured results with success/error information
   - Need to properly wrap these into standardized error responses

3. **Delivery Method Validation**:
   - Limited to specific enum values (STANDARD, ACCELERATED)
   - The API may have additional restrictions on allowed values

## 5. Expected Outcome

A fully refactored `budget.py` module with:
- Proper validation of all input parameters including budget-specific validations
- Standardized error handling with helpful, contextual error messages
- Consistent use of utility functions for validation, logging, error handling, and formatting
- Improved error context to aid in debugging
- Reduced code duplication through use of utility modules

## 6. Implementation Progress Tracking

- [ ] Added required imports from utility modules
- [ ] Replaced standard logger with get_logger
- [ ] Refactored get_budgets with validation and error handling
- [ ] Refactored get_budgets_json with validation and error handling
- [ ] Refactored analyze_budgets with validation and error handling
- [ ] Refactored update_budget with validation and error handling
- [ ] Tested with various valid and invalid inputs
- [ ] Updated implementation plan to mark budget.py as complete 