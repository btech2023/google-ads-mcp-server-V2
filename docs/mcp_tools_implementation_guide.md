# MCP Tools Implementation Guide

## Introduction

This guide documents the established patterns and best practices for implementing MCP (Model Context Protocol) tools in the Google Ads MCP Server. It serves as a reference for developers working on maintaining existing tool modules or creating new ones.

The modularization approach organizes tools into logical, domain-specific modules rather than a single monolithic file. This improves code maintainability, readability, and testability.

## Module Structure

### Directory Structure

```
google_ads_mcp_server/
├── mcp/
│   ├── tools/
│   │   ├── __init__.py         # Tool registration and imports
│   │   ├── health.py           # Health check tools
│   │   ├── budget.py           # Budget-related tools
│   │   ├── campaign.py         # Campaign-related tools
│   │   ├── ad_group.py         # Ad group-related tools
│   │   ├── keyword.py          # Keyword and search term tools
│   │   ├── dashboard.py        # Dashboard visualization tools
│   │   └── insights.py         # Insights and recommendation tools (planned)
│   └── ...
├── tests/
│   ├── unit/
│   │   ├── test_tools.py               # General tools tests
│   │   ├── test_budget_tools.py        # Budget-specific tests
│   │   ├── test_keyword_tools.py       # Keyword-specific tests
│   │   ├── test_dashboard_tools.py     # Dashboard-specific tests
│   │   └── ...
```

### Module Components

Each module follows a consistent structure:

1. **Module Docstring**: Brief description of the module purpose
2. **Imports**: Standard library imports, followed by internal imports
3. **Logger Initialization**: Standard logging setup
4. **Registration Function**: The main registration function that registers all tools in the module
5. **Tool Functions**: Individual tool functions decorated with `@mcp.tool()`

## File Template

```python
"""
[Module Name] Tools Module

This module contains [module topic]-related MCP tools.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from visualization.formatters import format_for_visualization
from visualization.[module_name] import format_[module_name]_visualization

logger = logging.getLogger(__name__)

def register_[module_name]_tools(mcp, google_ads_service, [module_name]_service) -> None:
    """
    Register [module name]-related MCP tools.
    
    Args:
        mcp: The MCP server instance
        google_ads_service: The Google Ads service instance
        [module_name]_service: The [module name] service instance
    """
    # Related: mcp.tools.[related_module].[related_function] ([relationship description])
    @mcp.tool()
    async def get_[entity_name](customer_id: str, [other_params]) -> str:
        """
        [Tool description].
        
        Args:
            customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
            [other_param_docs]
            
        Returns:
            [Return value description]
        """
        try:
            # Remove dashes from customer ID if present
            if customer_id and '-' in customer_id:
                customer_id = customer_id.replace('-', '')
                
            logger.info(f"[Log message for this operation]")
            
            # Call service method
            result = await [module_name]_service.[method_name](
                customer_id=customer_id,
                [other_params]
            )
            
            # Handle empty results
            if not result:
                return "[Appropriate message for empty results]"
            
            # Format with dashes for display
            display_customer_id = customer_id
            if display_customer_id and len(display_customer_id) == 10:
                display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
            
            # Format the results (text or JSON)
            # ...
            
            return [formatted_result]
            
        except Exception as e:
            logger.error(f"Error [doing operation]: {str(e)}")
            return f"Error: {str(e)}"
```

## Tool Function Patterns

### Tool Types

MCP tools generally fall into these categories:

1. **Text Report Tools**: Return formatted text for display, typically without the `_json` suffix
2. **JSON/Visualization Tools**: Return structured data with visualization objects, with the `_json` suffix
3. **Action Tools**: Perform operations like creating or updating entities
4. **Analysis Tools**: Perform analysis and return insights

### Naming Conventions

- **Get Operations**: `get_[entity]` or `get_[entity]_json`
- **Create Operations**: `create_[entity]`
- **Update Operations**: `update_[entity]`
- **Delete/Remove Operations**: `remove_[entity]` or `delete_[entity]`
- **Analysis Operations**: `analyze_[entity]` or `analyze_[entity]_json`

### Parameter Patterns

Common parameters across tools:

- `customer_id`: String in format "123-456-7890" or "1234567890"
- Entity IDs (e.g., `campaign_id`, `ad_group_id`): Strings representing the entity ID
- `date_range` or `start_date`/`end_date`: For date filtering
- Filters (e.g., `status`): For entity filtering
- `metrics`: For specifying which metrics to include

### Return Value Patterns

#### Text Report Format
```
[Title]
[Subtitle with customer_id/entity information]
[Date Range or other context]

[Headers with aligned columns]
----------------
[Data rows with aligned columns]
```

#### JSON Response Format
```python
{
    "type": "success",  # or "error"
    "data": {
        # Entity data
    },
    "visualization": {
        # Visualization object(s)
    }
}
```

#### Error Response Format
```python
{
    "type": "error",
    "message": "Error: [description]",
    # Additional context parameters like customer_id, entity_id, etc.
}
```

## Error Handling

All tool functions should:

1. Be wrapped in try/except blocks
2. Log errors with appropriate context
3. Return user-friendly error messages
4. Include relevant parameters in error responses for context

Example:
```python
try:
    # Tool implementation
except Exception as e:
    logger.error(f"Error getting campaign performance: {str(e)}")
    return f"Error: {str(e)}"  # for text tools
    # OR
    return {"type": "error", "message": f"Error: {str(e)}", "param": value}  # for JSON tools
```

## Documentation

### Tool Documentation

Each tool function should have:

1. A clear docstring describing its purpose
2. Complete parameter documentation
3. Return value documentation
4. Cross-module references for related tools

### Cross-Module Documentation

Add a `# Related:` comment before each tool that relates to tools in other modules:

```python
# Related: mcp.tools.campaign.get_campaigns (Account dashboard includes campaign data)
@mcp.tool()
async def get_account_dashboard_json(...):
```

## Testing

### Test File Structure

Each module should have a corresponding test file that:

1. Mocks the relevant services
2. Tests normal operation for each tool
3. Tests error handling for each tool
4. Tests edge cases (empty results, invalid parameters)

### Test Data Setup

Test files should include realistic test data that mirrors the actual API responses:

```python
def setUp(self):
    """Set up test fixtures."""
    self.mock_service = MagicMock(spec=ServiceClass)
    
    # Sample data for tests
    self.sample_data = [
        {
            "id": "123456",
            "name": "Test Entity",
            # Other fields
        }
    ]
```

### Mocking Pattern

Use `unittest.mock.patch` to mock dependencies:

```python
with patch('google_ads_mcp_server.mcp.tools.module_name.service_name', self.mock_service):
    result = tool_function(params)
```

## Service Integration

### Service Dependency Injection

Services are initialized in `__init__.py` and passed to registration functions:

```python
# In __init__.py
service_instance = ServiceClass(google_ads_service)
register_module_tools(mcp, google_ads_service, service_instance)

# In module.py
def register_module_tools(mcp, google_ads_service, module_service):
    # Tool definitions...
```

### Service Method Calls

Tool functions should:

1. Delegate actual API operations to the service
2. Focus on parameter validation, formatting, and error handling
3. Not contain business logic that belongs in the service layer

## Visualization Integration

### Visualization Patterns

1. **Text tools**: Return formatted strings
2. **JSON tools**: Return dictionaries with visualization objects

### Visualization Format
```python
visualization = {
    "chart_type": "bar|line|pie|table",
    "title": "Chart Title",
    # Other visualization properties
}
```

## Registration Process

### Module Registration

1. Create a new file for the module
2. Implement the registration function
3. Update `__init__.py` to import and call the registration function

### In `__init__.py`:
```python
# Import registration functions
from .module_name import register_module_name_tools

def register_tools(mcp, google_ads_service):
    # Initialize services
    from google_ads.module_name import ModuleNameService
    
    # Create service instances
    module_name_service = ModuleNameService(google_ads_service)
    
    # Register tools
    register_module_name_tools(mcp, google_ads_service, module_name_service)
```

## Best Practices Summary

1. **Consistent Structure**: Follow the established patterns for module structure and tool implementation
2. **Error Handling**: Implement comprehensive error handling in all tools
3. **Testing**: Create thorough tests for all tools, including error cases
4. **Documentation**: Document tools and their relationships to other tools
5. **Service Pattern**: Maintain separation between tool functions and service logic
6. **Parameter Validation**: Validate all parameters before calling services
7. **Formatting**: Format customer IDs and other outputs consistently
8. **Naming**: Use consistent naming conventions for tools and their parameters
9. **Code Style**: Follow PEP 8 guidelines for Python code style
10. **Semantic Cohesion**: Group tools by semantic relationship, not just technical hierarchy

## Implementation Checklist

When implementing a new tool module:

- [ ] Create module file with proper structure
- [ ] Create test file with comprehensive tests
- [ ] Implement all relevant tools for the domain
- [ ] Add cross-module documentation
- [ ] Update `__init__.py` to register the new module
- [ ] Verify with compilation/syntax checks
- [ ] Run tests if environment supports it
- [ ] Add cross-references from related modules

## Example Code Snippets

### Example Text Tool

```python
@mcp.tool()
async def get_campaigns(customer_id: str, status: str = None):
    """
    Get campaigns for a Google Ads account with optional filtering.
    
    Args:
        customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
        status: Optional status filter (ENABLED, PAUSED, REMOVED)
        
    Returns:
        Formatted list of campaigns
    """
    try:
        # Remove dashes from customer ID if present
        if customer_id and '-' in customer_id:
            customer_id = customer_id.replace('-', '')
            
        logger.info(f"Getting campaigns for customer ID {customer_id}")
        
        # Get campaigns using the CampaignService
        campaigns = await campaign_service.get_campaigns(
            customer_id=customer_id,
            status_filter=status
        )
        
        if not campaigns:
            return "No campaigns found with the specified filters."
        
        # Format with dashes for display
        display_customer_id = customer_id
        if display_customer_id and len(display_customer_id) == 10:
            display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
        
        # Format the results as a text report
        report = [
            f"Google Ads Campaigns",
            f"Account ID: {display_customer_id}",
            f"Status Filter: {status if status else 'All Statuses'}\n",
            f"{'Campaign ID':<15} {'Campaign Name':<30} {'Status':<15} {'Budget':<15} {'Channel':<20} {'Bidding Strategy':<20}",
            "-" * 115
        ]
        
        # Add data rows
        for campaign in sorted(campaigns, key=lambda x: x["name"]):
            # Format row data...
            report.append(
                f"{campaign['id']:<15} {name:<30} {campaign['status']:<15} "
                f"{budget:<15} {channel:<20} {bidding:<20}"
            )
            
        return "\n".join(report)
        
    except Exception as e:
        logger.error(f"Error getting campaigns: {str(e)}")
        return f"Error: {str(e)}"
```

### Example JSON Tool

```python
@mcp.tool()
async def get_account_dashboard_json(customer_id: str, date_range: str = "LAST_30_DAYS", comparison_range: str = "PREVIOUS_30_DAYS"):
    """
    Get a comprehensive account dashboard with KPIs, trends, and top performers.
    
    Args:
        customer_id: Google Ads customer ID (format: 123-456-7890 or 1234567890)
        date_range: Date range for the dashboard (e.g., LAST_30_DAYS, LAST_7_DAYS, LAST_90_DAYS)
        comparison_range: Period to compare against (e.g., PREVIOUS_30_DAYS, PREVIOUS_YEAR)
        
    Returns:
        JSON data for account dashboard visualization
    """
    try:
        # Remove dashes from customer ID if present
        if customer_id and '-' in customer_id:
            customer_id = customer_id.replace('-', '')
            
        logger.info(f"Getting account dashboard for customer ID {customer_id}")
        
        # Get dashboard data using the DashboardService
        dashboard_data = await dashboard_service.get_account_dashboard(
            customer_id=customer_id,
            date_range=date_range,
            comparison_range=comparison_range
        )
        
        if not dashboard_data or "error" in dashboard_data:
            error_message = dashboard_data.get("error", "Failed to retrieve account dashboard data")
            logger.error(f"Error getting account dashboard: {error_message}")
            return {
                "type": "error",
                "message": f"Error: {error_message}",
                "customer_id": customer_id,
                "date_range": date_range
            }
        
        # Format display customer ID with dashes for response
        display_customer_id = customer_id
        if display_customer_id and len(display_customer_id) == 10:
            display_customer_id = f"{display_customer_id[:3]}-{display_customer_id[3:6]}-{display_customer_id[6:]}"
        
        # Create visualization using the formatter
        visualization = create_account_dashboard_visualization(
            account_data=dashboard_data
        )
        
        # Return the formatted dashboard response
        return {
            "type": "success",
            "data": {
                "customer_id": display_customer_id,
                "date_range": date_range,
                "comparison_range": comparison_range,
                "account_name": dashboard_data.get("account_name", "My Account"),
                "metrics": dashboard_data.get("metrics", {}),
                "time_series": dashboard_data.get("time_series", []),
                "campaigns": dashboard_data.get("campaigns", []),
                "ad_groups": dashboard_data.get("ad_groups", [])
            },
            "visualization": visualization
        }
    except Exception as e:
        logger.error(f"Error getting account dashboard: {str(e)}")
        return {
            "type": "error",
            "message": f"Error: {str(e)}",
            "customer_id": customer_id,
            "date_range": date_range
        }
```

## Conclusion

Following these patterns and best practices will ensure consistency and maintainability across the Google Ads MCP Server codebase. As new modules are added or existing ones are enhanced, adhering to these guidelines will help maintain a cohesive architecture and facilitate easier debugging and testing. 