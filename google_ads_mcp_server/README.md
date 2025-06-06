# Google Ads MCP Server

A modular server for providing Google Ads data through the Model Context Protocol (MCP).

## Overview

This server provides access to Google Ads data through the MCP protocol, enabling AI assistants to interact with Google Ads accounts. The server exposes both MCP tools (function calling) and MCP resources for comprehensive data access.

## Project Structure

```
google_ads_mcp_server/
├── main.py                       # Application entry point
├── server.py                     # Core server (reduced size)
├── google_ads/                   # Google Ads specific modules  
│   ├── client.py                 # Core Google Ads client
│   ├── campaigns.py              # Campaign-related operations
│   ├── ad_groups.py              # Ad group-related operations
│   ├── keywords.py               # Keyword-related operations
│   └── reporting.py              # Reporting functionality
├── mcp/                          # MCP specific modules
│   ├── resources.py              # MCP resources implementation
│   ├── tools.py                  # MCP tools implementation 
│   └── handlers.py               # MCP request handlers
├── visualization/                # Visualization modules
│   ├── formatters.py             # Data formatting for visualization
│   ├── time_series.py            # Time series chart formatting
│   ├── comparisons.py            # Comparison chart formatting
│   └── campaign_charts.py        # Campaign-specific visualizations
├── db/                           # Database and caching
│   ├── manager.py                # Database manager
│   └── cache.py                  # Caching implementation
├── utils/                        # Utilities
│   ├── formatting.py             # General formatting utilities
│   ├── validation.py             # Input validation
│   ├── error_handler.py          # Error handling
│   └── logging.py                # Logging utilities
├── config.py                     # Configuration management
├── health.py                     # Health checks functionality
└── requirements.txt              # Project dependencies
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- A Google Ads developer account with API access
- Client credentials for the Google Ads API

### Installation

1. Clone the repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on the `.env.example` with your Google Ads API credentials.

### Running the Server

```
python -m google_ads_mcp_server.main
```

This will start the server on the default port 8000. The MCP endpoint will be available at `/mcp`.

## Features

- Access to Google Ads accounts and hierarchy
- Campaign performance reporting
- Ad group management
- Keyword data
- Performance metrics visualization

## Development

When adding new features, follow these principles:

1. Add new domain-specific functions to the appropriate module in `google_ads/`
2. Implement new MCP tools in `mcp/tools.py`
3. Add visualization formatters in the `visualization/` directory
4. Update tests in the `tests/` directory

## License

Copyright (c) 2023-2025 