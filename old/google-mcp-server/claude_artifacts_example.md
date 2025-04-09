# Using Google Ads MCP Server with Claude Artifacts

This guide demonstrates how to use the JSON data provided by the Google Ads MCP server to create visualizations with Claude Artifacts.

## Prerequisites

1. A running instance of the Google Ads MCP server
2. Access to Claude Desktop or API with Artifacts support

## JSON Tools Overview

The Google Ads MCP server provides the following JSON-based tools:

- `get_accounts_json`: Lists all accessible Google Ads accounts
- `get_account_hierarchy_json`: Gets the Google Ads account hierarchy
- `get_campaign_performance_json`: Gets performance metrics for campaigns
- `get_account_summary_json`: Gets summary metrics for an account

## Example Visualizations

### 1. Account Hierarchy Visualization

```python
# Example Claude prompt to create account hierarchy visualization

import json
from mcp_client import MCPClient

# Connect to the MCP server
client = MCPClient("http://localhost:8000")

# Get account hierarchy data
hierarchy_json = client.call_tool("get_account_hierarchy_json")
hierarchy_data = json.loads(hierarchy_json)

# Create visualization with Claude Artifacts
"""
Here's a visualization of the Google Ads account hierarchy:

<chart type="tree" title="Google Ads Account Hierarchy" showLegend="false">
  {
    "name": "${hierarchy_data['name']}",
    "id": "${hierarchy_data['id']}",
    "children": ${json.dumps(hierarchy_data['children'])}
  }
</chart>
"""
```

### 2. Campaign Performance Comparison

```python
# Example Claude prompt to create campaign performance visualization

import json
from mcp_client import MCPClient

# Connect to the MCP server
client = MCPClient("http://localhost:8000")

# Get campaign performance data
campaign_json = client.call_tool("get_campaign_performance_json")
campaign_data = json.loads(campaign_json)

# Create a bar chart visualization with Claude Artifacts
"""
Here's a visualization of campaign performance:

<chart type="bar" title="Campaign Performance by Cost" 
       xAxis="Campaign" yAxis="Cost ($)" height="500">
  {
    "data": [
      ${','.join([f'{{"Campaign": "{c["name"]}", "Cost": {c["cost"]}, "Clicks": {c["clicks"]}}}' for c in campaign_data["campaigns"][:10]])}
    ]
  }
</chart>
"""
```

### 3. Account Summary Metrics

```python
# Example Claude prompt to create account metrics visualization

import json
from mcp_client import MCPClient

# Connect to the MCP server
client = MCPClient("http://localhost:8000")

# Get account summary data
summary_json = client.call_tool("get_account_summary_json")
summary_data = json.loads(summary_json)

# Create a metrics dashboard with Claude Artifacts
"""
## Google Ads Account Performance Dashboard

Account ID: ${summary_data['customer_id']}
Date Range: ${summary_data['date_range']['start_date']} to ${summary_data['date_range']['end_date']}

<chart type="metric" title="Key Performance Indicators">
  {
    "metrics": [
      {"name": "Impressions", "value": ${summary_data['total_impressions']}, "prefix": "", "suffix": ""},
      {"name": "Clicks", "value": ${summary_data['total_clicks']}, "prefix": "", "suffix": ""},
      {"name": "Cost", "value": ${summary_data['total_cost']}, "prefix": "$", "suffix": ""},
      {"name": "CTR", "value": ${summary_data['ctr']}, "prefix": "", "suffix": "%"},
      {"name": "CPC", "value": ${summary_data['cpc']}, "prefix": "$", "suffix": ""},
      {"name": "Conversions", "value": ${summary_data['total_conversions']}, "prefix": "", "suffix": ""},
      {"name": "Conversion Rate", "value": ${summary_data['conversion_rate']}, "prefix": "", "suffix": "%"},
      {"name": "Cost per Conversion", "value": ${summary_data['cost_per_conversion']}, "prefix": "$", "suffix": ""}
    ]
  }
</chart>
"""
```

### 4. Multi-Account Comparison

```python
# Example Claude prompt to create multi-account comparison

import json
from mcp_client import MCPClient

# Connect to the MCP server
client = MCPClient("http://localhost:8000")

# Get account list
accounts_json = client.call_tool("get_accounts_json")
accounts_data = json.loads(accounts_json)

# Get data for the first 5 accounts
account_data = []
for account in accounts_data["accounts"][:5]:
    summary_json = client.call_tool("get_account_summary_json", {"customer_id": account["id"]})
    account_data.append(json.loads(summary_json))

# Create comparison visualization with Claude Artifacts
"""
## Multi-Account Performance Comparison

<chart type="bar" title="Account Performance Comparison" 
       xAxis="Account" yAxis="Metrics" height="400">
  {
    "data": [
      ${','.join([f'{{"Account": "{i+1}", "Cost": {d["total_cost"]}, "Clicks": {d["total_clicks"]}, "Conversions": {d["total_conversions"]}}}' for i, d in enumerate(account_data)])}
    ]
  }
</chart>
"""
```

## Tips for Working with Claude Artifacts

1. **Data Formatting**: Claude Artifacts expects data in a specific format for each chart type. Refer to the Artifacts documentation for details.

2. **JSON Handling**: Always handle potential JSON parsing errors in your code.

3. **Dynamic Content**: Use string interpolation to insert dynamic data into the visualization.

4. **Error Handling**: Include error checking to handle cases where the MCP server returns error messages instead of data.

## Deployment Considerations

When integrating the Google Ads MCP server with Claude for visualization:

1. **Caching**: The MCP server implements caching to reduce API calls to Google Ads, but consider additional caching if creating many visualizations.

2. **Authentication**: Ensure your Google Ads credentials are properly secured.

3. **Rate Limits**: Be mindful of Google Ads API rate limits when generating multiple visualizations in quick succession. 