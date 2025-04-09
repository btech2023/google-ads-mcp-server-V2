# Visualization Data Format Specification for Google Ads KPI MCP Server
**Date: 2025-03-27**

## 1. Introduction

This document specifies the JSON data formats required for visualizing Google Ads KPI data within Claude Artifacts. It outlines the structure and formatting requirements to ensure compatibility with Claude's supported visualization libraries, primarily Recharts, Chart.js, and React components.

### 1.1 Purpose

To establish a standardized approach for formatting Google Ads KPI data in a JSON structure that enables direct visualization within Claude Artifacts, ensuring consistency across all visualization types and data scenarios.

### 1.2 Scope

This specification covers:
- JSON data structures for various visualization types
- Field naming conventions and required attributes
- Data transformation requirements from Google Ads API to visualization format
- Examples of properly formatted data for each visualization type

## 2. Claude Artifacts Visualization Capabilities

### 2.1 Supported Libraries

Claude Artifacts supports several JavaScript visualization libraries, with the following being directly integrated:

1. **Recharts** - Primary library for React-based chart components
2. **Chart.js** - Alternative library for canvas-based visualizations
3. **D3.js** - For more complex or custom visualizations
4. **React components** - For building custom visualization interfaces

### 2.2 Visualization Types

The Google Ads KPI MCP Server should support the following visualization types:

1. **Time Series Charts** - For performance metrics over time
2. **Bar Charts** - For campaign comparisons and metric breakdowns
3. **Pie/Donut Charts** - For distribution analysis (e.g., campaign types)
4. **Comparison Charts** - For period-over-period analysis
5. **Tables** - For detailed metric display
6. **KPI Cards** - For summary metrics with trend indicators

## 3. JSON Structure Templates

### 3.1 Time Series Chart Format

```json
{
  "chart_type": "time_series",
  "title": "Campaign Performance Over Time",
  "subtitle": "Daily metrics from [start_date] to [end_date]",
  "data": [
    {
      "date": "2025-03-20",
      "impressions": 12500,
      "clicks": 780,
      "cost": 1250.75,
      "conversions": 45
    },
    {
      "date": "2025-03-21",
      "impressions": 13200,
      "clicks": 820,
      "cost": 1320.50,
      "conversions": 52
    }
    // Additional days...
  ],
  "axes": {
    "x": {
      "label": "Date",
      "dataKey": "date",
      "type": "category"
    },
    "y": {
      "label": "Value",
      "type": "number"
    }
  },
  "series": [
    {
      "name": "Impressions",
      "dataKey": "impressions",
      "color": "#8884d8",
      "type": "line"
    },
    {
      "name": "Clicks",
      "dataKey": "clicks",
      "color": "#82ca9d",
      "type": "line"
    },
    {
      "name": "Cost ($)",
      "dataKey": "cost",
      "color": "#ffc658",
      "type": "line"
    },
    {
      "name": "Conversions",
      "dataKey": "conversions",
      "color": "#ff8042",
      "type": "line"
    }
  ],
  "legend": true,
  "grid": true,
  "tooltip": true
}
```

### 3.2 Bar Chart Format

```json
{
  "chart_type": "bar",
  "title": "Campaign Performance Comparison",
  "subtitle": "Key metrics by campaign",
  "data": [
    {
      "campaign_name": "Brand Search",
      "impressions": 45000,
      "clicks": 3200,
      "cost": 4500.75,
      "conversions": 320
    },
    {
      "campaign_name": "Generic Search",
      "impressions": 120000,
      "clicks": 6800,
      "cost": 12500.50,
      "conversions": 450
    }
    // Additional campaigns...
  ],
  "axes": {
    "x": {
      "label": "Campaign",
      "dataKey": "campaign_name",
      "type": "category"
    },
    "y": {
      "label": "Value",
      "type": "number"
    }
  },
  "series": [
    {
      "name": "Clicks",
      "dataKey": "clicks",
      "color": "#82ca9d",
      "type": "bar"
    },
    {
      "name": "Conversions",
      "dataKey": "conversions",
      "color": "#ff8042",
      "type": "bar"
    }
  ],
  "legend": true,
  "grid": true,
  "tooltip": true
}
```

### 3.3 Pie Chart Format

```json
{
  "chart_type": "pie",
  "title": "Campaign Type Distribution",
  "subtitle": "Budget allocation by campaign type",
  "data": [
    {
      "name": "Search",
      "value": 45000.75,
      "color": "#8884d8"
    },
    {
      "name": "Display",
      "value": 32000.50,
      "color": "#82ca9d"
    },
    {
      "name": "Video",
      "value": 18500.25,
      "color": "#ffc658"
    },
    {
      "name": "Shopping",
      "value": 22000.10,
      "color": "#ff8042"
    }
  ],
  "dataKey": "value",
  "nameKey": "name",
  "colorKey": "color",
  "legend": true,
  "tooltip": true,
  "innerRadius": 0,       // Set > 0 for donut chart
  "outerRadius": "80%",
  "label": true
}
```

### 3.4 Period Comparison Chart Format

```json
{
  "chart_type": "comparison",
  "title": "Period-over-Period Performance",
  "subtitle": "This week vs. last week",
  "data": [
    {
      "metric": "Impressions",
      "current_period": 125000,
      "previous_period": 112000,
      "percent_change": 11.6
    },
    {
      "metric": "Clicks",
      "current_period": 7800,
      "previous_period": 7200,
      "percent_change": 8.3
    },
    {
      "metric": "Cost",
      "current_period": 12500.75,
      "previous_period": 11800.50,
      "percent_change": 5.9
    },
    {
      "metric": "Conversions",
      "current_period": 450,
      "previous_period": 420,
      "percent_change": 7.1
    }
  ],
  "axes": {
    "x": {
      "label": "Metric",
      "dataKey": "metric",
      "type": "category"
    },
    "y": {
      "label": "Value",
      "type": "number"
    }
  },
  "series": [
    {
      "name": "Current Period",
      "dataKey": "current_period",
      "color": "#8884d8",
      "type": "bar"
    },
    {
      "name": "Previous Period",
      "dataKey": "previous_period",
      "color": "#82ca9d",
      "type": "bar"
    }
  ],
  "percent_change_format": "+0.0%",
  "legend": true,
  "grid": true,
  "tooltip": true
}
```

### 3.5 Table Format

```json
{
  "chart_type": "table",
  "title": "Campaign Performance Details",
  "columns": [
    {
      "title": "Campaign",
      "dataKey": "campaign_name",
      "width": 200
    },
    {
      "title": "Impressions",
      "dataKey": "impressions",
      "width": 120,
      "format": "number"
    },
    {
      "title": "Clicks",
      "dataKey": "clicks",
      "width": 100,
      "format": "number"
    },
    {
      "title": "CTR",
      "dataKey": "ctr",
      "width": 80,
      "format": "percent"
    },
    {
      "title": "Cost",
      "dataKey": "cost",
      "width": 100,
      "format": "currency"
    },
    {
      "title": "Conversions",
      "dataKey": "conversions",
      "width": 120,
      "format": "number"
    },
    {
      "title": "CPA",
      "dataKey": "cpa",
      "width": 100,
      "format": "currency"
    }
  ],
  "data": [
    {
      "campaign_name": "Brand Search",
      "impressions": 45000,
      "clicks": 3200,
      "ctr": 7.11,
      "cost": 4500.75,
      "conversions": 320,
      "cpa": 14.06
    },
    {
      "campaign_name": "Generic Search",
      "impressions": 120000,
      "clicks": 6800,
      "ctr": 5.67,
      "cost": 12500.50,
      "conversions": 450,
      "cpa": 27.78
    }
    // Additional campaigns...
  ],
  "pagination": true,
  "sortable": true,
  "defaultSort": "cost",
  "defaultSortDirection": "desc"
}
```

### 3.6 KPI Card Format

```json
{
  "chart_type": "kpi_cards",
  "title": "Performance Summary",
  "data": [
    {
      "title": "Impressions",
      "value": 125000,
      "previous_value": 112000,
      "percent_change": 11.6,
      "trend_direction": "up",
      "format": "number",
      "color": "#8884d8"
    },
    {
      "title": "Clicks",
      "value": 7800,
      "previous_value": 7200,
      "percent_change": 8.3,
      "trend_direction": "up",
      "format": "number",
      "color": "#82ca9d"
    },
    {
      "title": "Cost",
      "value": 12500.75,
      "previous_value": 11800.50,
      "percent_change": 5.9,
      "trend_direction": "up",
      "format": "currency",
      "color": "#ffc658"
    },
    {
      "title": "Conversions",
      "value": 450,
      "previous_value": 420,
      "percent_change": 7.1,
      "trend_direction": "up",
      "format": "number",
      "color": "#ff8042"
    }
  ],
  "comparison_label": "vs. Previous Period",
  "layout": "horizontal",
  "card_width": 250,
  "card_height": 150
}
```

## 4. Google Ads Metrics Mapping

### 4.1 Core Metrics Mapping

| Google Ads API Metric         | JSON Field Name | Format Type | Description                              |
|-------------------------------|-----------------|-------------|------------------------------------------|
| metrics.impressions           | impressions     | number      | Number of ad impressions                 |
| metrics.clicks                | clicks          | number      | Number of ad clicks                      |
| metrics.cost_micros / 1000000 | cost            | currency    | Cost in account currency                 |
| metrics.conversions           | conversions     | number      | Number of conversions                    |
| metrics.conversions_value     | conversion_value| currency    | Value of conversions in account currency |
| metrics.ctr                   | ctr             | percent     | Click-through rate (clicks/impressions)  |
| metrics.average_cpc / 1000000 | cpc             | currency    | Average cost per click                   |
| metrics.average_cpm / 1000000 | cpm             | currency    | Average cost per thousand impressions    |
| metrics.cost_per_conversion   | cpa             | currency    | Cost per acquisition (cost/conversions)  |
| metrics.roas                  | roas            | decimal     | Return on ad spend (value/cost)          |

### 4.2 Dimension Mapping

| Google Ads API Dimension         | JSON Field Name | Format Type | Description                              |
|---------------------------------|-----------------|-------------|------------------------------------------|
| campaign.name                   | campaign_name   | string      | Campaign name                            |
| campaign.advertising_channel_type | campaign_type   | string      | Campaign type (SEARCH, DISPLAY, etc.)    |
| campaign.status                 | campaign_status | string      | Campaign status                          |
| ad_group.name                   | ad_group_name   | string      | Ad group name                            |
| segments.date                   | date            | date        | Date in YYYY-MM-DD format               |
| segments.day_of_week            | day_of_week     | string      | Day of week (Monday, Tuesday, etc.)      |
| segments.device                 | device          | string      | Device type                              |

### 4.3 Derived Metrics

| Derived Metric  | Formula                            | JSON Field Name | Format Type | Description                   |
|-----------------|-----------------------------------|-----------------|-------------|-------------------------------|
| CTR             | clicks / impressions * 100         | ctr             | percent     | Click-through rate            |
| CPA             | cost / conversions                 | cpa             | currency    | Cost per acquisition          |
| ROAS            | conversion_value / cost            | roas            | decimal     | Return on ad spend            |
| Percent Change  | (current - previous) / previous * 100 | percent_change | percent     | Period-over-period change     |

## 5. Data Transformation

### 5.1 API Response to Visualization Format

The following process should be used to transform Google Ads API responses into visualization-ready JSON:

1. **Extract metrics and dimensions** from the Google Ads API response
2. **Convert unit values** (e.g., micros to currency)
3. **Calculate derived metrics** (CTR, CPA, ROAS)
4. **Structure data according to visualization type**
5. **Add metadata** (chart type, titles, axes, series)

### 5.2 Transformation Code Example

```python
def format_time_series_data(api_response):
    """
    Transform Google Ads API response to time series chart format.
    
    Args:
        api_response: Raw response from Google Ads API
        
    Returns:
        JSON object formatted for time series visualization
    """
    # Extract data points
    data_points = []
    for row in api_response:
        data_point = {
            "date": row.segments.date,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": row.metrics.cost_micros / 1000000,  # Convert micros to currency
            "conversions": row.metrics.conversions
        }
        
        # Add derived metrics
        if data_point["impressions"] > 0:
            data_point["ctr"] = (data_point["clicks"] / data_point["impressions"]) * 100
        else:
            data_point["ctr"] = 0
            
        if data_point["conversions"] > 0:
            data_point["cpa"] = data_point["cost"] / data_point["conversions"]
        else:
            data_point["cpa"] = 0
            
        data_points.append(data_point)
    
    # Sort by date
    data_points.sort(key=lambda x: x["date"])
    
    # Create visualization JSON
    visualization_data = {
        "chart_type": "time_series",
        "title": "Campaign Performance Over Time",
        "subtitle": f"Daily metrics from {data_points[0]['date']} to {data_points[-1]['date']}",
        "data": data_points,
        "axes": {
            "x": {
                "label": "Date",
                "dataKey": "date",
                "type": "category"
            },
            "y": {
                "label": "Value",
                "type": "number"
            }
        },
        "series": [
            {
                "name": "Impressions",
                "dataKey": "impressions",
                "color": "#8884d8",
                "type": "line"
            },
            {
                "name": "Clicks",
                "dataKey": "clicks",
                "color": "#82ca9d",
                "type": "line"
            },
            {
                "name": "Cost ($)",
                "dataKey": "cost",
                "color": "#ffc658",
                "type": "line"
            },
            {
                "name": "Conversions",
                "dataKey": "conversions",
                "color": "#ff8042",
                "type": "line"
            }
        ],
        "legend": True,
        "grid": True,
        "tooltip": True
    }
    
    return visualization_data
```

## 6. Claude Artifacts Integration

### 6.1 Rendering in Claude Artifacts

When sending data to Claude for visualization, the JSON structure should be included in the MCP response. Claude will automatically render the visualization based on the provided data and chart configuration.

### 6.2 Artifact Type Mapping

| Visualization Type | Claude Artifact Type   | Description                         |
|--------------------|------------------------|-------------------------------------|
| Time Series        | application/vnd.ant.react | React component with Recharts      |
| Bar Chart          | application/vnd.ant.react | React component with Recharts      |
| Pie Chart          | application/vnd.ant.react | React component with Recharts      |
| Table              | application/vnd.ant.react | React component with styling       |
| KPI Cards          | application/vnd.ant.react | React component with styling       |

### 6.3 MCP Response Example

```json
{
  "response": {
    "message": "Here's your Google Ads performance data.",
    "visualization_data": {
      "chart_type": "time_series",
      "title": "Campaign Performance Over Time",
      "data": [...],
      "axes": {...},
      "series": [...]
    }
  }
}
```

## 7. Implementation Guidelines

### 7.1 Naming Conventions

- Use camelCase for all JSON field names
- Use descriptive names that align with visualization library expectations
- Maintain consistent naming across all visualization types
- Prefix internal fields with underscore (e.g., `_metadata`)

### 7.2 Data Validation

Before sending data for visualization, validate that:

1. All required fields are present
2. Data types are correct (numbers, strings, dates)
3. Date formats are consistent (YYYY-MM-DD)
4. Arrays have at least one element
5. Required nested objects exist

### 7.3 Error Handling

When data is incomplete or invalid for visualization:

1. Provide meaningful error messages in the MCP response
2. Fall back to simpler visualization types when possible
3. Include debug information to help identify the issue
4. Log validation errors for monitoring

## 8. Testing and Validation

### 8.1 Test Scenarios

Test visualizations with the following scenarios:

1. **Basic data set** - Simple data with expected values
2. **Empty data set** - No data points available
3. **Large data set** - Many data points (100+)
4. **Extreme values** - Very large or small numbers
5. **Missing fields** - Some fields not available
6. **Zero values** - Metrics with zero values
7. **Null values** - Metrics with null values

### 8.2 Validation Process

For each test scenario:

1. Generate test data matching the scenario
2. Transform into visualization format
3. Validate the JSON structure
4. Test rendering in Claude Artifacts
5. Verify visual correctness
6. Document any issues or limitations

## 9. References

1. Recharts Documentation: https://recharts.org/
2. Chart.js Documentation: https://www.chartjs.org/
3. Google Ads API Documentation: https://developers.google.com/google-ads/api/docs/start
4. Claude Artifacts Documentation: [Reference Documentation]
