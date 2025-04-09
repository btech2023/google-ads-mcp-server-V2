# MCP Tools Modularization

This directory contains the modularized implementation of MCP tools for the Google Ads MCP Server.

## Overview

The MCP tools have been refactored from a monolithic `tools.py` file into separate modules, each focused on a specific category of tools.

## Tool Modules

The following modules have been implemented:

| Module | Description | Key Tools |
|--------|-------------|-----------|
| `health.py` | Health check and system status tools | `check_api_connection` |
| `budget.py` | Budget-related tools | `get_budgets`, `get_budgets_json`, `update_budget` |
| `campaign.py` | Campaign-related tools | `get_campaigns`, `get_campaign_performance`, `create_campaign` |
| `ad_group.py` | Ad group-related tools | `get_ad_groups`, `create_ad_group`, `update_ad_group` |
| `keyword.py` | Keyword-related tools | `get_keywords`, `add_keywords`, `update_keyword` |
| `search_term.py` | Search term-related tools | `get_search_terms_report`, `analyze_search_terms` |
| `dashboard.py` | Dashboard and reporting tools | `get_account_dashboard_json`, `get_campaign_dashboard_json` |
| `insights.py` | Analytics and insights tools | `get_performance_anomalies`, `get_optimization_suggestions`, `get_opportunities` |

## Implementation Details

Each module follows the same pattern:

1. Imports the necessary dependencies
2. Defines a `register_X_tools` function (where X is the module name)
3. Implements MCP tool functions decorated with `@mcp.tool()` within the `register_X_tools` function

The `__init__.py` file is responsible for:

1. Importing all `register_X_tools` functions from the individual modules
2. Defining the main `register_tools` function that creates the necessary service instances
3. Calling all the individual `register_X_tools` functions with the appropriate services

## Cross-Module Documentation

To maintain discoverability and aid in navigation, tools contain `# Related:` comments linking to related tools in other modules. For example:

```python
# Related: mcp.tools.ad_group.get_ad_groups (Keywords belong to ad groups)
@mcp.tool()
async def get_keywords(...):
    """Get keywords for a Google Ads account"""
    # ... implementation ...
```

This helps developers understand relationships between tools across different modules.

## Integration Testing

After implementing each module, integration tests verify that:

1. The server starts correctly with the registered tools
2. Tools are registered properly with the MCP instance
3. Tools can be called with appropriate parameters
4. Cross-module dependencies work correctly

## Backward Compatibility

For backward compatibility, select tool functions are re-exported in `__init__.py` to maintain existing imports that may rely on the old structure. 