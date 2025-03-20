# NOVA: Nimble Operational Visualization Application
## MVP Implementation Plan
**Date: 2025-03-18**

## Overview

Building on the foundation established through SAGE, PRISM, and STELLAR, this NOVA implementation plan outlines the final steps required to deliver a working Google Ads KPI MCP Server MVP. The plan focuses on creating a lightweight, practical solution that leverages our existing visualization capabilities to present the last 7 days of core Google Ads metrics.

## Core Objectives

1. Create a fully functional Google Ads MCP Server using Python
2. Focus exclusively on visualizing last 7 days of performance 
3. Present clear, actionable visualizations of core KPIs
4. Minimize configuration requirements for quick deployment
5. Create comprehensive yet simple documentation

## Implementation Phases

### Phase 1: Core API Implementation

**Objective:** Establish reliable Google Ads API connection with minimal configuration

**Tasks:**
1. Implement simplified Google Ads API client
   - Focus exclusively on basic metrics (cost, conversions, clicks, impressions, etc.)
   - Limit to last 7 days of data by default
   - Create efficient GAQL queries for optimal performance
   - Implement automatic retry and error handling

2. Create streamlined configuration
   - Define minimal required credentials
   - Create environment variable config option
   - Add simple YAML config file alternative
   - Implement credential validation

3. Establish data normalization layer
   - Create consistent data structures for KPIs
   - Implement automatic unit conversion (micros → currency)
   - Add derived metrics calculation (CPA, ROAS, etc.)

**Expected Duration:** 3 days

### Phase 2: Default Dashboard Creation

**Objective:** Design a compelling default dashboard experience

**Tasks:**
1. Define default KPI set
   - Cost, Conversions, Cost per Conversion
   - Clicks, Impressions, CTR
   - Conversion Value, ROAS
   - Avg. Position, Impression Share (if available)

2. Create standard visualization set
   - Time series of daily performance
   - Period-over-period comparison (yesterday vs same day last week)
   - KPI summary with trend indicators
   - Campaign performance breakdown
   - Device/platform distribution

3. Implement automatic data interpretation
   - Add trend detection and highlighting
   - Include performance anomaly detection
   - Create simple natural language insights

**Expected Duration:** 4 days

### Phase 3: MCP Protocol Integration

**Objective:** Connect visualization capabilities to Claude via MCP

**Tasks:**
1. Define MCP resources and endpoints
   - Create `/default-dashboard` resource
   - Add `/kpi/{metric_name}` resources for individual metrics
   - Implement `/campaigns` resource for campaign-level data

2. Implement MCP server handlers
   - Create handler for default dashboard visualization
   - Add custom KPI visualization handlers
   - Implement campaign data visualization handler

3. Optimize MCP payload structure
   - Ensure compatibility with Claude Artifacts
   - Minimize payload size for efficient processing
   - Add metadata for proper rendering context

**Expected Duration:** 3 days

### Phase 4: Deployment Package

**Objective:** Create a deployment-ready package

**Tasks:**
1. Create installation package
   - Prepare `setup.py` or `pyproject.toml`
   - Define minimal dependencies
   - Add version constraints for stability
   - Create versioning strategy

2. Implement CLI interface
   - Add command for running the server
   - Create configuration validation command
   - Include connection testing utility
   - Add simple server status check

3. Prepare Docker deployment option
   - Create minimal Dockerfile
   - Add docker-compose.yml for easy deployment
   - Include environment variable support
   - Document Docker deployment process

**Expected Duration:** 2 days

### Phase 5: Documentation & Testing

**Objective:** Ensure the product is well-documented and tested

**Tasks:**
1. Create comprehensive documentation
   - Write installation guide
   - Add configuration documentation
   - Create getting started walkthrough
   - Include troubleshooting section

2. Implement core tests
   - Add unit tests for API client
   - Create integration tests for MCP server
   - Implement end-to-end test with mock API
   - Add documentation tests

3. Create example prompts for Claude
   - Design sample prompts for dashboard retrieval
   - Create examples for KPI visualization
   - Add campaign analysis prompt examples
   - Include real-world usage scenarios

**Expected Duration:** 3 days

## Technical Specifications

### Data Structure

The NOVA MVP will focus on the following core Google Ads metrics:

```python
DEFAULT_METRICS = {
    "cost": {
        "api_name": "metrics.cost_micros",
        "transform": lambda x: x / 1000000,  # Convert micros to currency
        "format": "currency"
    },
    "conversions": {
        "api_name": "metrics.conversions",
        "transform": lambda x: x,  # No transformation needed
        "format": "decimal_1"
    },
    "clicks": {
        "api_name": "metrics.clicks", 
        "transform": lambda x: x,
        "format": "number"
    },
    "impressions": {
        "api_name": "metrics.impressions",
        "transform": lambda x: x,
        "format": "number"
    },
    "conversion_value": {
        "api_name": "metrics.conversion_value",
        "transform": lambda x: x,
        "format": "currency"
    },
    # Derived metrics
    "ctr": {
        "derived": True,
        "formula": lambda m: (m["clicks"] / m["impressions"]) * 100 if m["impressions"] > 0 else 0,
        "format": "percentage_2"
    },
    "cpa": {
        "derived": True,
        "formula": lambda m: m["cost"] / m["conversions"] if m["conversions"] > 0 else 0,
        "format": "currency"
    },
    "roas": {
        "derived": True, 
        "formula": lambda m: m["conversion_value"] / m["cost"] if m["cost"] > 0 else 0,
        "format": "decimal_2"
    }
}
```

### API Integration

The Google Ads API integration will be streamlined to focus on recent data:

```python
DEFAULT_QUERY_TEMPLATE = """
SELECT
  segments.date,
  campaign.id,
  campaign.name,
  campaign.status,
  campaign.advertising_channel_type,
  metrics.cost_micros,
  metrics.conversions,
  metrics.clicks,
  metrics.impressions,
  metrics.conversion_value
FROM campaign
WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
ORDER BY segments.date DESC
"""

def get_default_date_range():
    """Return default date range (last 7 days)"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    return {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }
```

### Visualization Structure

Standard visualizations will include:

1. **Time Series Chart**
```json
{
  "title": "Last 7 Days Performance",
  "data": [
    {"date": "2025-03-11", "Cost": 120.50, "Conversions": 5.2, "Clicks": 420},
    {"date": "2025-03-12", "Cost": 135.25, "Conversions": 6.1, "Clicks": 450},
    "..."
  ],
  "chartType": "line",
  "labels": {"x": "Date", "y": "Value"}
}
```

2. **KPI Summary Cards**
```json
{
  "cards": [
    {
      "title": "Cost",
      "value": "$1,245.75", 
      "trend": "+5.2%",
      "trend_direction": "up",
      "comparison_label": "vs last week"
    },
    "..."
  ]
}
```

3. **Campaign Breakdown**
```json
{
  "title": "Campaign Performance",
  "data": [
    {"name": "Brand Campaign", "Cost": 523.50, "Conversions": 12.3, "ROAS": 3.2},
    {"name": "Generic Search", "Cost": 752.25, "Conversions": 8.7, "ROAS": 1.9},
    "..."
  ],
  "chartType": "bar",
  "labels": {"x": "Campaign", "y": "Value"}
}
```

### MCP Protocol Integration

The MCP server will provide the following resources:

```
google-ads://dashboard                     # Complete dashboard visualization
google-ads://kpi/{metric_name}             # Individual KPI visualization 
google-ads://campaigns                     # Campaign performance breakdown
google-ads://time-series/{metric_names}    # Custom time series chart
```

## Success Criteria

The NOVA MVP will be considered successful when:

1. A user can run the server with minimal configuration
2. The server connects to Google Ads API and retrieves last 7 days of data
3. Claude can request and display visualizations via the MCP protocol
4. Core KPIs (cost, conversions, ROAS) are clearly presented
5. Installation and usage is documented with step-by-step instructions

## Expected Deliverables

1. `google-ads-mcp-server` Python package
2. Installation and configuration documentation
3. Example Claude prompts for visualization
4. Docker deployment configuration
5. Basic test suite

## Timeline

Total expected duration: **15 working days**

- Phase 1 (Core API Implementation): 3 days
- Phase 2 (Default Dashboard Creation): 4 days
- Phase 3 (MCP Protocol Integration): 3 days
- Phase 4 (Deployment Package): 2 days
- Phase 5 (Documentation & Testing): 3 days

## Getting Started Guide (Preview)

```markdown
# Google Ads MCP Server - Quick Start

## Installation

```bash
pip install google-ads-mcp-server
```

## Configuration

1. Create a `.env` file with your Google Ads credentials:

```
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
GOOGLE_ADS_CLIENT_ID=your_client_id
GOOGLE_ADS_CLIENT_SECRET=your_client_secret
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_CUSTOMER_ID=your_customer_id
```

2. Run the server:

```bash
google-ads-mcp start
```

3. In Claude, use the following prompt:

```
I'd like to see my Google Ads performance for the last 7 days.
Please connect to the MCP server to retrieve and visualize my KPI data.
```
```

---

*This plan may be referenced using the shorthand "@NOVA" in future discussions.*
