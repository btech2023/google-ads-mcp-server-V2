# Google Ads MCP Server Modularization Strategy

## Overview

With the server.py file reaching over 2,000 lines, a modularization strategy is essential for maintainability, readability, and scalability. This document outlines a comprehensive approach to breaking down the monolithic server.py file into a well-structured, modular codebase that maintains alignment with the MCP protocol architecture while organizing around Google Ads domain entities.

## Recommended Directory Structure

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

## Implementation Strategy

### Phase 1: Initial Setup (1-2 days)
1. Create the directory structure
2. Set up proper imports between files
3. Create a minimal version of each module with placeholder functions
4. Move configuration to config.py

### Phase 2: Extract Google Ads Functionality (2-3 days)
1. Move Google Ads client core functionality to google_ads/client.py
2. Refactor entity-specific code to respective files (campaigns.py, ad_groups.py, etc.)
3. Update imports to reflect the new structure
4. Test each module individually

### Phase 3: Extract MCP Components (2-3 days)
1. Move MCP resources to mcp/resources.py
2. Move MCP tools to mcp/tools.py
3. Move request handlers to mcp/handlers.py
4. Update server.py to import and register these components

### Phase 4: Extract Visualization Logic (1-2 days)
1. Move visualization formatting to the visualization/ directory
2. Separate by chart type and entity
3. Create consistent interfaces for visualization formatters

### Phase 5: Utilities and Database (1-2 days)
1. Extract utility functions to the utils/ directory
2. Move database and caching logic to db/ directory
3. Create proper abstraction layers

### Phase 6: Finalize and Test (2-3 days)
1. Update server.py to be a thin orchestration layer
2. Implement comprehensive tests for all modules
3. Test the entire application
4. Update documentation

## Code Examples

### Example 1: Main Application Entry Point (main.py)

```python
import logging
from config import load_config
from server import create_server
from health import setup_health_checks
from mcp.handlers import register_mcp_handlers

def main():
    # Load configuration
    config = load_config()
    
    # Setup logging
    logging.basicConfig(level=config.log_level)
    
    # Create server
    app = create_server(config)
    
    # Register MCP handlers
    register_mcp_handlers(app)
    
    # Setup health checks
    setup_health_checks(app)
    
    # Run server
    app.run(host=config.host, port=config.port)

if __name__ == "__main__":
    main()
```

### Example 2: Core Server (server.py)

```python
from fastapi import FastAPI
from mcp import sse_app
from google_ads.client import GoogleAdsService
from db.manager import DatabaseManager
from config import Config

def create_server(config: Config):
    # Initialize FastAPI app
    app = FastAPI(title="Google Ads MCP Server", version="1.0.0")
    
    # Initialize database manager
    db_manager = DatabaseManager(config.db_path)
    
    # Initialize Google Ads service
    google_ads_service = GoogleAdsService(config, db_manager)
    
    # Mount MCP server
    app.mount("/mcp", sse_app())
    
    # Store services in app state
    app.state.google_ads_service = google_ads_service
    app.state.db_manager = db_manager
    app.state.config = config
    
    @app.on_event("startup")
    async def startup():
        # Initialize database
        db_manager.initialize_db()
    
    @app.on_event("shutdown")
    async def shutdown():
        # Close database connections
        db_manager.close()
    
    return app
```

### Example 3: Google Ads Client (google_ads/client.py)

```python
from google.ads.googleads.client import GoogleAdsClient
from db.cache import CacheManager
import logging

logger = logging.getLogger(__name__)

class GoogleAdsService:
    def __init__(self, config, db_manager):
        self.config = config
        self.db_manager = db_manager
        self.cache_manager = CacheManager(db_manager)
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        try:
            return GoogleAdsClient.load_from_dict(self.config.google_ads)
        except Exception as e:
            logger.error(f"Failed to initialize Google Ads client: {e}")
            raise
    
    def get_customer(self, customer_id):
        # Implementation
        pass
    
    def get_service(self, service_name):
        # Get specific Google Ads service
        return self.client.get_service(service_name)
    
    def get_query_builder(self):
        # Get query builder
        return self.client.get_type("GoogleAdsFieldService")
    
    def execute_query(self, customer_id, query, retry_count=3):
        """
        Execute a GAQL query with retry logic and proper error handling
        """
        # Implementation
        pass
```

### Example 4: Campaign Service (google_ads/campaigns.py)

```python
import logging
from datetime import datetime
from utils.formatting import format_date, micros_to_currency

logger = logging.getLogger(__name__)

class CampaignService:
    def __init__(self, google_ads_service):
        self.google_ads_service = google_ads_service
        self.ga_service = google_ads_service.get_service("GoogleAdsService")
    
    def get_campaigns(self, customer_id, status_filter=None):
        """
        Get all campaigns for a customer
        
        Args:
            customer_id: Google Ads customer ID
            status_filter: Optional filter for campaign status
            
        Returns:
            List of campaign data
        """
        # Build query
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                campaign_budget.amount_micros
            FROM campaign
        """
        
        # Add status filter if provided
        if status_filter:
            query += f" WHERE campaign.status = '{status_filter}'"
        
        # Execute query
        response = self.google_ads_service.execute_query(customer_id, query)
        
        # Format response
        campaigns = []
        for row in response:
            campaign = {
                "id": row.campaign.id,
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "channel_type": row.campaign.advertising_channel_type.name,
                "bidding_strategy": row.campaign.bidding_strategy_type.name if row.campaign.bidding_strategy_type else None,
                "budget": micros_to_currency(row.campaign_budget.amount_micros) if row.campaign_budget.amount_micros else None
            }
            campaigns.append(campaign)
        
        return campaigns
    
    def get_performance(self, customer_id, start_date, end_date, metrics=None):
        """
        Get campaign performance data
        
        Args:
            customer_id: Google Ads customer ID
            start_date: Start date for performance data
            end_date: End date for performance data
            metrics: Optional list of metrics to include
            
        Returns:
            Campaign performance data
        """
        # Implementation
        pass
```

### Example 5: MCP Tools (mcp/tools.py)

```python
from google_ads.campaigns import CampaignService
from google_ads.ad_groups import AdGroupService
from google_ads.reporting import ReportingService
from visualization.formatters import format_for_visualization

class MCPTools:
    def __init__(self, google_ads_service):
        self.google_ads_service = google_ads_service
        self.campaign_service = CampaignService(google_ads_service)
        self.ad_group_service = AdGroupService(google_ads_service)
        self.reporting_service = ReportingService(google_ads_service)
    
    def get_campaigns(self, params):
        """
        MCP tool to get campaign list
        """
        # Get data from service
        campaigns = self.campaign_service.get_campaigns(
            params["customer_id"],
            params.get("status_filter")
        )
        
        # Format response
        return {
            "type": "success",
            "data": campaigns
        }
    
    def get_campaign_performance(self, params):
        """
        MCP tool to get campaign performance
        """
        # Get data from service
        data = self.campaign_service.get_performance(
            params["customer_id"],
            params["start_date"],
            params["end_date"],
            params.get("metrics")
        )
        
        # Format response
        return {
            "type": "success",
            "data": data
        }
    
    def get_campaign_performance_json(self, params):
        """
        MCP tool to get campaign performance in JSON format for visualization
        """
        # Get data from service
        data = self.campaign_service.get_performance(
            params["customer_id"],
            params["start_date"],
            params["end_date"],
            params.get("metrics")
        )
        
        # Format for visualization
        visualization_data = format_for_visualization(
            data, 
            chart_type="time_series",
            metrics=params.get("metrics", ["clicks", "impressions", "cost"])
        )
        
        # Format response
        return {
            "type": "success",
            "data": data,
            "visualization": visualization_data
        }
```

### Example 6: MCP Resources (mcp/resources.py)

```python
class MCPResources:
    def __init__(self, google_ads_service):
        self.google_ads_service = google_ads_service
    
    async def read_resource(self, uri):
        """
        MCP resource reader implementation
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource data
        """
        parts = uri.path.strip("/").split("/")
        
        if uri.scheme != "google-ads":
            raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
        
        # Handle different resource types
        if parts[0] == "campaigns":
            if len(parts) == 2:
                # Single campaign
                customer_id = uri.query.get("customer_id")
                campaign_id = parts[1]
                return self._get_campaign(customer_id, campaign_id)
            else:
                # Campaign list
                customer_id = uri.query.get("customer_id")
                return self._get_campaigns(customer_id)
        elif parts[0] == "ad_groups":
            # Ad group resources
            pass
        elif parts[0] == "performance":
            # Performance data
            pass
        else:
            raise ValueError(f"Unknown resource type: {parts[0]}")
    
    def _get_campaign(self, customer_id, campaign_id):
        """
        Get single campaign data
        """
        # Implementation
        pass
    
    def _get_campaigns(self, customer_id):
        """
        Get all campaigns
        """
        # Implementation
        pass
```

### Example 7: Visualization Formatter (visualization/formatters.py)

```python
def format_for_visualization(data, chart_type, metrics=None):
    """
    Format data for visualization in Claude Artifacts
    
    Args:
        data: Raw data to format
        chart_type: Type of chart (time_series, bar, pie, etc.)
        metrics: List of metrics to include
        
    Returns:
        Formatted data for visualization
    """
    if chart_type == "time_series":
        from visualization.time_series import format_time_series
        return format_time_series(data, metrics)
    elif chart_type == "bar":
        from visualization.comparisons import format_bar_chart
        return format_bar_chart(data, metrics)
    elif chart_type == "pie":
        from visualization.campaign_charts import format_pie_chart
        return format_pie_chart(data, metrics)
    elif chart_type == "table":
        from visualization.formatters import format_table
        return format_table(data, metrics)
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")
```

### Example 8: Database Manager (db/manager.py)

```python
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="cache.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def initialize_db(self):
        """
        Initialize database and create tables if they don't exist
        """
        try:
            # Ensure directory exists
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Connect to database
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            
            # Create account_kpi_cache table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_kpi_cache (
                    cache_key TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    segmentation_json TEXT NOT NULL,
                    kpi_data_json TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_account_id ON account_kpi_cache(account_id)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_dates ON account_kpi_cache(start_date, end_date)
            """)
            
            self.conn.commit()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_kpi_data(self, cache_key):
        """
        Get cached KPI data
        """
        try:
            self.cursor.execute(
                "SELECT kpi_data_json FROM account_kpi_cache WHERE cache_key = ?",
                (cache_key,)
            )
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get KPI data: {e}")
            return None
    
    def store_kpi_data(self, cache_key, account_id, start_date, end_date, segmentation_json, kpi_data_json):
        """
        Store KPI data in cache
        """
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO account_kpi_cache
                (cache_key, account_id, start_date, end_date, segmentation_json, kpi_data_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (cache_key, account_id, start_date, end_date, segmentation_json, kpi_data_json))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store KPI data: {e}")
            return False
    
    def is_cache_valid(self, cache_key, max_age_minutes=15):
        """
        Check if cache is still valid
        """
        # Implementation
        pass
    
    def clear_cache(self):
        """
        Clear all cached data
        """
        try:
            self.cursor.execute("DELETE FROM account_kpi_cache")
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def close(self):
        """
        Close database connection
        """
        if self.conn:
            self.conn.close()
```

## Benefits of This Approach

### 1. Improved Maintainability
- Smaller, focused files are easier to understand and modify
- Clear separation of concerns between different modules
- Changes to one component are less likely to affect others

### 2. Better Code Organization
- Logical grouping of related functionality
- Clear directory structure that follows both MCP architecture and Google Ads domain
- Easy to locate specific functionality

### 3. Enhanced Collaboration
- Multiple developers can work on different modules simultaneously
- Reduced merge conflicts when changes are isolated to specific modules
- Clearer ownership of different components

### 4. Easier Testing
- Each module can be tested independently
- Simplified mock creation for dependencies
- Improved test coverage through more focused tests

### 5. Scalability
- New features can be added to appropriate modules without bloating the main server file
- Additional Google Ads entities can be added as new modules
- Visualization capabilities can be extended independently

### 6. Reduced Cognitive Load
- Developers can focus on smaller, more manageable chunks of code
- Clear interfaces between modules make interactions more predictable
- Improved developer productivity through better code organization

## Implementation Notes

1. **Maintain Backward Compatibility**: Ensure the modularized code maintains the same functionality as the original monolithic file.

2. **Incremental Approach**: Implement the modularization incrementally, testing after each phase to ensure everything still works.

3. **Documentation**: Update documentation to reflect the new structure as you go.

4. **Interface Stability**: Define clear, stable interfaces between modules to minimize interdependencies.

5. **Dependency Injection**: Use dependency injection to provide services to components that need them.

6. **Consistent Error Handling**: Maintain consistent error handling patterns across all modules.

7. **Logging**: Implement comprehensive logging to aid in debugging and monitoring.

8. **Configuration Management**: Centralize configuration in the config.py file to avoid duplication.

## Conclusion

This modularization strategy provides a clear path to transform the monolithic server.py file into a well-structured, maintainable codebase. By organizing code around both Google Ads domain entities and the MCP protocol architecture, the resulting structure will be intuitive, scalable, and aligned with best practices in software design. The phased implementation approach ensures that the transition can be made smoothly while maintaining a functioning system throughout the process.
