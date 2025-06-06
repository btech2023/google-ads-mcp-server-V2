# Google Ads MCP Server

*Updated on May 22, 2025 - Phase 5 Automated Insights Features Implementation Complete*

A Model Context Protocol (MCP) server that provides access to Google Ads data through Claude Desktop.

## Features

- Access Google Ads campaigns, accounts, and performance metrics via Claude
- Budget Management API Endpoints with visualizations (Project Quantum Pulse Phase 3)
- Keyword Management API Endpoints with visualizations (Project Quantum Pulse Phase 2)
- Ad Group Management API Endpoints (Project Quantum Pulse Phase 1)
- Support for both Manager (MCC) and client account data
- Built-in caching to improve performance and reduce API calls
- Claude Artifacts integration for data visualization
- Multi-environment support (development, testing, production)
- Containerized deployment with Docker

## Project Quantum Pulse Roadmap

This repository implements the Project Quantum Pulse roadmap for enhanced Google Ads management capabilities:

### Phase 1: Ad Group Management API Endpoints (COMPLETE) - March 29 to April 4, 2025
- Get ad groups with filtering capabilities
- View ad group performance metrics
- Create new ad groups
- Update existing ad groups
- Visualize ad group performance

### Phase 2: Keyword Management API Endpoints (COMPLETE) - April 5 to April 18, 2025
- Browse keywords with filtering capabilities ✅
- Analyze search terms and find insights ✅
- Add, update, and remove keywords ✅
- Visualize keyword performance with tables, charts, and word clouds ✅

### Phase 3: Budget Management API Endpoints (COMPLETE) - April 19 to May 2, 2025
- Retrieve campaign budgets with performance metrics ✅
- Analyze budget utilization and distribution ✅
- Generate budget recommendations ✅
- Visualize budget performance with charts and tables ✅
- Update budget properties (API call implementation pending)

### Phase 4: Enhanced Visualization Templates (COMPLETE) - May 3 to May 16, 2025
- Implement comprehensive dashboard templates ✅
- Create comparison visualization templates ✅
- Build breakdown visualization templates ✅
- Integration, testing, and documentation ✅

### Phase 5: Automated Insights Features (COMPLETE) - May 17 to May 30, 2025
- Implement performance anomaly detection ✅
- Generate optimization suggestions ✅
- Discover growth opportunities ✅
- Create integrated insights dashboard ✅

## Prerequisites

- Python 3.9 or higher
- Google Ads API credentials
- Claude Desktop

## Setup Overview

This project can be run in several different environments. Choose the setup that best fits your workflow:

1. [Python Virtual Environment](#python-virtual-environment)
2. [Docker](#docker)
   - [Docker for Linux/macOS](#docker-for-linuxmacos)
   - [Docker for Windows](#docker-for-windows)
   - [Docker Compose](#docker-compose)
3. [Kubernetes](#kubernetes-deployment)

## Python Virtual Environment

Follow these steps to run the MCP server using a local Python virtual environment:

1. **Clone this repository**
   ```bash
   git clone https://github.com/yourusername/google-ads-mcp-server-V2.git
   cd google-ads-mcp-server-V2
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   # Linux / macOS
   source .venv/bin/activate
   # Windows
   .venv\Scripts\activate
   ```

3. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```
   OpenTelemetry dependencies are pinned to version 1.21.0 to avoid
   resolver backtracking errors during installation.

4. **Configure Google Ads credentials**
   - Go to the [Google Ads API Console](https://developers.google.com/google-ads/api/docs/first-call/oauth-cloud) and create OAuth2 credentials.
   - Generate a refresh token following the Google Ads instructions.
   - Copy `.env.example` to `.env` and fill in the values you obtained:
     ```bash
     cp .env.example .env
     # Edit .env with your developer token, client ID, client secret and refresh token
     ```

5. **Start the server**
   ```bash
   python -m google_ads_mcp_server.main
   ```
   Visit `http://localhost:8000/health` to confirm the server is running.

## Docker

### Docker for Linux/macOS

1. **Build the image**
   ```bash
   docker build -t google-ads-mcp:latest -f docker/Dockerfile .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env google-ads-mcp:latest
   ```

### Docker for Windows

1. **Build the image**
   ```powershell
   docker build -t google-ads-mcp:latest -f docker/Dockerfile .
   ```

2. **Run the container**
   ```powershell
   docker run -p 8000:8000 --env-file .env google-ads-mcp:latest
   ```

### Docker Compose

Start all services defined in the compose file:
```bash
docker compose -f docker/docker-compose.yml up -d
```

## Kubernetes Deployment

This repository includes manifests for deploying the server to Kubernetes:

- `kubernetes/dev/` - development environment
- `kubernetes/test/` - test environment
- `kubernetes/prod/` - production environment

CI/CD pipelines are configured using GitHub Actions for automated testing, building and deployment.

Apply the manifests with `kubectl` for your chosen environment:

```bash
kubectl apply -f kubernetes/dev
```

Replace `dev` with `test` or `prod` to target another environment.

## Configuration

The application supports different environments (dev, test, prod) with environment-specific configurations:

- Set `APP_ENV` to `dev`, `test`, or `prod` to specify the environment
- Configure environment variables as documented in `.env.example`
- Feature flags allow enabling/disabling specific functionality

## Claude Desktop Integration

1. Configure Claude Desktop for the MCP server in your Claude Desktop App configuration. Replace `/path/to/project` with the folder where you cloned the repository:
   ```json
   {
       "mcpServers": {
           "google-ads": {
               "command": "python",
               "args": [
                    "/path/to/project/google_ads_mcp_server/main.py"
               ]
           }
       }
   }
   ```

2. Restart Claude Desktop and look for the tools icon to appear

3. Use Google Ads data in Claude by asking questions like:
   - "Show me my Google Ads account performance"
   - "What campaigns are performing well in my account?"
   - "Create a visualization of my campaign performance"
   - "List all ad groups in my 123-456-7890 account"
   - "Update the status of ad group 12345678 to PAUSED"
   - "Create a new ad group called 'Summer Products 2025' in campaign 98765432"

## Ad Group Management Tools

The following MCP tools are available for ad group management:

| Tool | Description |
|------|-------------|
| `get_ad_groups` | Get ad groups for a Google Ads account with optional filtering |
| `get_ad_groups_json` | Get ad groups in JSON format for visualization |
| `get_ad_group_performance` | Get performance metrics for a specific ad group |
| `get_ad_group_performance_json` | Get ad group performance metrics in JSON format for visualization |
| `create_ad_group` | Create a new ad group within a campaign |
| `update_ad_group` | Update an existing ad group's attributes |

## Keyword Management Tools

The following MCP tools are available for keyword management:

| Tool | Description |
|------|-------------|
| `get_keywords` | Get keywords for a Google Ads account with optional filtering |
| `get_keywords_json` | Get keywords in JSON format for visualization |
| `add_keywords` | Add a new keyword to an ad group |
| `update_keyword` | Update an existing keyword's status or bid |
| `remove_keywords` | Remove keywords from an ad group |
| `get_search_terms_report` | View search terms that triggered your ads |
| `get_search_terms_report_json` | Get search terms in JSON format for visualization |
| `analyze_search_terms` | Get insights about your search terms performance |
| `analyze_search_terms_json` | Get insights about your search terms performance in JSON format for visualization |

Example usage in Claude:
- "List all keywords in my 123-456-7890 account"
- "Show me search terms for campaign 12345678"
- "Add a broad match keyword 'summer shoes' to ad group 87654321"
- "Pause keyword 12345" 
- "Analyze search terms in my account to find opportunities"

## Budget Management Tools

The following MCP tools are available for budget management:

| Tool | Description |
|------|-------------|
| `get_budgets` | Get campaign budgets with performance metrics and utilization |
| `get_budgets_json` | Get budget information in JSON format with visualizations |
| `analyze_budgets` | Analyze budget performance with insights and recommendations |
| `update_budget` | Update a budget's amount or delivery method (placeholder implementation) |

Example usage in Claude:
- "Show me all campaign budgets in my account"
- "Analyze budget utilization across my campaigns"
- "Visualize budget distribution by campaign"
- "Which budgets are being depleted too quickly?"
- "What are the budget recommendations for my account?"
- "Update the daily budget for campaign 12345678 to $100"

Example response for `get_budgets`:
```
Budget Report (3 budgets found)

ID: 123456789
Name: Search Campaign Budget
Amount: 50.00 USD (Daily)
Status: ENABLED
Utilization: 65.4%
Associated Campaigns: Brand Search, Generic Search

ID: 987654321
Name: Display Campaign Budget
Amount: 100.00 USD (Daily)
Status: ENABLED
Utilization: 94.2%
Associated Campaigns: Retargeting Display, Prospecting Display

ID: 456789123
Name: Shopping Campaign Budget
Amount: 75.00 USD (Daily)
Status: ENABLED
Utilization: 32.1%
Associated Campaigns: Product Shopping
```

Example response for `analyze_budgets`:
```
Budget Analysis Report

Budget: Display Campaign Budget (ID: 987654321)
Amount: 100.00 USD (Daily)
Utilization: 94.2%
Associated Campaigns: Retargeting Display, Prospecting Display
Insights:
- High Utilization (94.2%)
- Budget nearly depleted before day end
Recommendations:
- Consider increasing budget to 120.00 USD
- Or reduce bid adjustments during peak hours

Budget: Search Campaign Budget (ID: 123456789)
Amount: 50.00 USD (Daily)
Utilization: 65.4%
Associated Campaigns: Brand Search, Generic Search
Insights:
- Moderate Utilization (65.4%)
- Performing well within budget constraints
Recommendations:
- Monitor performance
- Consider reallocating budget to high-performing campaigns

Budget: Shopping Campaign Budget (ID: 456789123)
Amount: 75.00 USD (Daily)
Utilization: 32.1%
Associated Campaigns: Product Shopping
Insights:
- Low Utilization (32.1%)
- Budget consistently underutilized
Recommendations:
- Consider reducing budget to 50.00 USD
- Or reallocate budget to higher-performing campaigns
```

## Enhanced Visualization Tools

The following MCP tools provide rich data visualization and advanced analysis capabilities:

### Dashboard Visualization Tools

| Tool | Description |
|------|-------------|
| `get_account_dashboard_json` | Get a comprehensive account dashboard with KPIs, trends, and top performers |
| `get_campaign_dashboard_json` | Get a detailed dashboard for a specific campaign |

Example usage in Claude:
- "Show me an account dashboard for the last 30 days"
- "Create a dashboard for campaign 12345678"
- "Compare my account performance to the previous month"
- "Show a dashboard with all my campaign KPIs"

The account dashboard includes:
- KPI cards with period-over-period comparisons
- Performance trend charts for key metrics
- Top campaigns and ad groups by performance
- Cost distribution visualizations

The campaign dashboard includes:
- Campaign overview and details
- KPI cards with period-over-period comparisons
- Performance trend charts
- Ad group breakdown
- Device performance distribution
- Top keywords

### Comparison Visualization Tools

| Tool | Description |
|------|-------------|
| `get_performance_comparison_json` | Compare metrics between multiple entities (campaigns, ad groups) |

Example usage in Claude:
- "Compare campaigns 123456 and 789012"
- "Show me a side-by-side comparison of my top 3 campaigns"
- "Compare clicks and conversions across my search campaigns"
- "Which campaign has better performance, 123456 or 789012?"

The comparison visualizations include:
- Side-by-side bar charts for key metrics
- Detailed comparison tables with absolute and relative differences
- Radar charts for multi-metric comparisons (when 3+ metrics are selected)

### Breakdown Visualization Tools

| Tool | Description |
|------|-------------|
| `get_performance_breakdown_json` | Break down performance by various dimensions (device, geo, time, etc.) |

Example usage in Claude:
- "Break down campaign 123456 performance by device"
- "Show my account performance by day of week"
- "What's the geographic distribution of my ad spend?"
- "Break down campaign 123456 by device and time"

The breakdown visualizations include:
- Stacked bar charts for categorical dimensions (device, network, geo)
- Line charts for time dimensions (day, week, month)
- Treemap charts for hierarchical data visualization
- Detailed tables with segment metrics and percentage contribution

Example response for `get_account_dashboard_json`:
```json
{
  "date_range": "LAST 30 DAYS",
  "comparison_range": "PREVIOUS 30 DAYS",
  "visualization": {
    "charts": [
      {
        "type": "line",
        "title": "Cost Trend",
        "data": { ... }
      },
      {
        "type": "line",
        "title": "Engagement Trend",
        "data": { ... }
      },
      {
        "type": "doughnut",
        "title": "Cost Distribution by Campaign",
        "data": { ... }
      }
    ],
    "tables": [
      {
        "title": "Account Performance",
        "type": "kpi_cards",
        "cards": [ ... ]
      },
      {
        "title": "Top Campaigns by Spend",
        "headers": ["Campaign", "Budget", "Status", "Cost"],
        "rows": [ ... ]
      }
    ]
  }
}
```

## Automated Insights Tools

The following MCP tools provide automated insights and recommendations based on account data analysis:

### Anomaly Detection Tools

| Tool | Description |
|------|-------------|
| `get_performance_anomalies` | Detect significant changes in performance metrics across campaigns, ad groups, or keywords |
| `get_performance_anomalies_json` | Get performance anomaly data in JSON format with visualizations |

Example usage in Claude:
- "Find performance anomalies in my account for the last 7 days"
- "Detect unusual changes in my campaign performance"
- "Which metrics have significant changes compared to last week?"
- "Analyze my account for performance issues"

The performance anomaly detection includes:
- Statistical analysis to identify outliers in key metrics
- Comparison against previous periods
- Severity scoring for detected anomalies
- Visualization of anomalies by metric and entity
- Ranked list of most significant changes

### Optimization Suggestion Tools

| Tool | Description |
|------|-------------|
| `get_optimization_suggestions` | Generate actionable optimization suggestions for an account |
| `get_optimization_suggestions_json` | Get optimization suggestions in JSON format with visualizations |

Example usage in Claude:
- "What optimizations should I make to my account?"
- "Suggest ways to improve my campaign performance"
- "Give me optimization ideas for my keywords"
- "How can I better allocate my budget?"

The optimization suggestions include:
- Bid management recommendations (increase/decrease bids)
- Budget allocation recommendations
- Negative keyword suggestions
- Ad copy improvement recommendations
- Account structure suggestions

### Opportunity Discovery Tools

| Tool | Description |
|------|-------------|
| `get_opportunities` | Discover growth opportunities in a Google Ads account |
| `get_opportunities_json` | Get growth opportunities in JSON format with visualizations |

Example usage in Claude:
- "Find growth opportunities in my account"
- "What search terms should I add as keywords?"
- "Where can I expand my advertising reach?"
- "Discover new keyword opportunities based on search terms"

The opportunity discovery includes:
- Keyword expansion suggestions based on high-performing search terms
- Ad variation recommendations for top ad groups
- Account structure optimization opportunities
- Prioritized list of actions by potential impact

### Integrated Insights Tool

| Tool | Description |
|------|-------------|
| `get_account_insights_json` | Get comprehensive account insights combining anomalies, suggestions, and opportunities |

Example usage in Claude:
- "Give me a complete analysis of my account"
- "What's the overall health of my Google Ads campaigns?"
- "Show me everything I should know about my account"
- "Generate a comprehensive insights report"

The integrated insights dashboard includes:
- Summary statistics and key findings
- Tabs for anomalies, suggestions, and opportunities
- Prioritized recommendations
- Interactive visualizations for each insight type

Example response for `get_performance_anomalies`:
```
Google Ads Performance Anomalies
Account ID: 123-456-7890
Entity Type: CAMPAIGN
Date Range: 2025-05-15 to 2025-05-22
Comparison Period: PREVIOUS_PERIOD
Total Anomalies Detected: 3

Entity Name                    Metric          Current      Previous     Change        Severity
----------------------------------------------------------------------------------------------
Search - Brand Terms           clicks          250          180          +38.9%        MEDIUM
Display - Retargeting          cost            $452.18      $325.45      +38.9%        MEDIUM
Shopping - Products            impressions     5,420        8,750        -38.1%        HIGH
```

Example response for `get_optimization_suggestions`:
```
Google Ads Optimization Suggestions
Account ID: 123-456-7890
Date Range: 2025-04-22 to 2025-05-22
Total Suggestions: 5

Budget Allocation Suggestions (2)
--------------------------------------------------
HIGH: Increase budget for campaign 'Search - Generic Terms' which is limited by budget (currently at 98% utilization)
     Action: Consider increasing the budget by 10-20% to allow for growth

MEDIUM: Campaign 'Display - Awareness' is significantly under budget (only 45% utilized)
     Action: Consider decreasing the budget to improve overall account efficiency, or reallocate to better-performing campaigns

Bid Management Suggestions (2)
--------------------------------------------------
HIGH: Keyword 'summer shoes sale' has strong conversion rate (8.5%) at $12.50 per conversion
     Action: Increase bid by 10-15% to capture more traffic for this high-performing keyword

MEDIUM: Keyword 'generic footwear' has high CPC ($2.75) with no conversions after 45 clicks
     Action: Decrease bid by 25-30% or pause if performance doesn't improve

Negative Keywords Suggestions (1)
--------------------------------------------------
MEDIUM: Add 'free shoes' as a negative keyword - spent $45.25 with no conversions
     Action: Add 'free shoes' as a negative exact match keyword to prevent further wasted spend
```

Example response for `get_opportunities`:
```
Google Ads Growth Opportunities
Account ID: 123-456-7890
Date Range: 2025-04-22 to 2025-05-22
Total Opportunities: 4

Keyword Expansion Opportunities (2)
--------------------------------------------------
HIGH: Add 'summer sandals women' as a keyword in ad group 'Women's Footwear'
     Action: Add 'summer sandals women' as an exact match keyword to better control bidding and relevance

MEDIUM: Add 'designer shoes discount' as a keyword in ad group 'Designer Collection'
     Action: Add 'designer shoes discount' as an exact match keyword to better control bidding and relevance

Ad Variation Opportunities (2)
--------------------------------------------------
MEDIUM: Create additional ad variations for ad group 'Men's Dress Shoes'
     Action: Add at least one more responsive search ad to test different headlines and descriptions

MEDIUM: Create additional ad variations for ad group 'Women's Athletic Shoes'
     Action: Add at least one more responsive search ad to test different headlines and descriptions
```


## Security

- All credentials are stored in Kubernetes secrets or environment variables, never in code
- The server uses proper authentication for API access
- Rate limiting is enabled in production environments
- Container security best practices are followed

## Testing

Run the test suite:
```
pytest
```

Run specific tests:
```
# Test Ad Group functionality
python -m google_ads_mcp_server.tests.unit.test_ad_groups

# Test Keyword functionality
python -m google_ads_mcp_server.tests.unit.test_keywords

# Test Budget functionality
python -m google_ads_mcp_server.tests.unit.test_budgets

# Test MCP Tools
python -m google_ads_mcp_server.tests.unit.test_tools

# Test Visualization formatters
python -m google_ads_mcp_server.tests.unit.test_visualizations

# Test Budget Visualizations
python -m google_ads_mcp_server.tests.unit.test_budget_visualizations
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Google Ads API team for their documentation and support
- Anthropic for Claude and the Model Context Protocol 