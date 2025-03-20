# SAGE-Plan: Structured Approach for Google-ads Enhancement
**Date: 2025-03-17**

## Overview
This implementation plan outlines the approach for enhancing the Google Ads KPI MCP Server prototype with a focus on testing, stability, and data visualization capabilities. The plan addresses four key areas: SQLite-based caching, unit testing, real-world testing, and visualization optimization.

## 1. SQLite Database Implementation

### 1.1 SQLite Schema Creation
- **Task**: Create database schema according to Backend Schema Document
- **Details**:
  - Create an `account_kpi_cache` table with:
    - `cache_key` (TEXT, PRIMARY KEY): Unique key based on account ID, date range, and segmentation
    - `account_id` (TEXT): Google Ads Account ID
    - `start_date` (TEXT): Start date (YYYY-MM-DD)
    - `end_date` (TEXT): End date (YYYY-MM-DD)
    - `segmentation_json` (TEXT): JSON representation of segmentation parameters
    - `kpi_data_json` (TEXT): JSON representation of cost and conversion data
    - `created_at` (TIMESTAMP): When data was cached
    - `updated_at` (TIMESTAMP): When cache entry was last updated
  - Implement indexes on: `account_id`, `start_date`, `end_date`, and `segmentation_json`

### 1.2 Database Manager Class
- **Task**: Create a `DatabaseManager` class to handle database operations
- **Details**:
  - Implement methods:
    - `__init__(db_path="cache.db")`: Initialize connection
    - `initialize_db()`: Create tables if not exist
    - `get_kpi_data(cache_key)`: Retrieve cached data
    - `store_kpi_data(cache_key, account_id, start_date, end_date, segmentation_json, kpi_data_json)`: Cache data
    - `is_cache_valid(cache_key, max_age_minutes=15)`: Check if cache is fresh
    - `clear_cache()`: Clear all cached data
    - `close()`: Close database connection

### 1.3 Integration with Google Ads Client
- **Task**: Modify `GoogleAdsClient` to use SQLite cache instead of in-memory cache
- **Details**:
  - Replace `self._cache` dictionary with database interactions
  - Update `get_kpis()` and `get_period_comparison()` methods to:
    - Check for valid cache entries in database
    - Store new data in database
    - Use timestamp-based cache invalidation

## 2. Unit Test Implementation

### 2.1 Google Ads Client Tests
- **Task**: Create comprehensive unit tests for `google_ads_client.py`
- **Details**:
  - Create `tests/test_google_ads_client.py` with test classes:
    - `TestGoogleAdsClientInitialization`: Test client initialization and authentication
    - `TestGoogleAdsClientKPIRetrieval`: Test KPI data retrieval, using mock Google Ads API responses
    - `TestGoogleAdsClientComparison`: Test period comparison functionality
    - `TestGoogleAdsClientCaching`: Test SQLite caching function
    - `TestGoogleAdsClientErrorHandling`: Test error handling for API failures

### 2.2 MCP Server Tests
- **Task**: Create unit tests for the MCP server implementation
- **Details**:
  - Create `tests/test_server.py` with test classes:
    - `TestServerResources`: Test resource listing and retrieval
    - `TestServerPrompts`: Test prompt listing and generation
    - `TestServerTools`: Test tool listing and execution
    - `TestServerIntegration`: Test integration with Google Ads client

### 2.3 Database Manager Tests
- **Task**: Create unit tests for the database manager
- **Details**:
  - Create `tests/test_database_manager.py` with:
    - Tests for database initialization
    - Tests for cache storage and retrieval
    - Tests for cache validation and expiration
    - Tests for thread safety (if applicable)

### 2.4 Integration Tests
- **Task**: Create integration tests to verify system behavior
- **Details**:
  - Create `tests/test_integration.py` with end-to-end scenarios:
    - Requesting KPI data via MCP
    - Saving to cache
    - Retrieving from cache
    - Testing cache invalidation
    - Testing error propagation

### 2.5 Test Fixtures and Mocks
- **Task**: Create test fixtures and mocks for testing
- **Details**:
  - Create mock Google Ads API responses
  - Create database fixtures
  - Create mock MCP clients for testing server responses

## 3. Google Ads API Integration Testing

### 3.1 Environment Configuration
- **Task**: Set up testing environment for Google Ads API
- **Details**:
  - Create a `.env.example` file with required variables:
    ```
    GOOGLE_ADS_DEVELOPER_TOKEN=your_token
    GOOGLE_ADS_CLIENT_ID=your_client_id
    GOOGLE_ADS_CLIENT_SECRET=your_client_secret
    GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
    GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_customer_id
    ```
  - Document the process for creating test credentials
  - Configure a test Google Ads account for development

### 3.2 Manual Integration Tests
- **Task**: Create a script for manual testing with real credentials
- **Details**:
  - Create `scripts/test_api_integration.py` that:
    - Loads credentials from `.env` file
    - Tests connection to Google Ads API
    - Retrieves real campaign data
    - Performs period comparisons
    - Logs results for verification

### 3.3 Live Testing with Claude Desktop
- **Task**: Test the MCP server with Claude Desktop
- **Details**:
  - Create testing scenarios:
    - Basic KPI retrieval
    - Segmented KPI requests
    - Period comparisons
    - Error handling cases
  - Document results and issues found

## 4. Visualization Data Formatting

### 4.1 Data Structure Analysis
- **Task**: Analyze how data should be structured for visualization
- **Details**:
  - Review Claude Artifacts visualization capabilities
  - Identify optimal data structures for:
    - Bar charts (campaign performance comparison)
    - Line charts (time-series performance data)
    - Pie charts (channel distribution)
    - Tables (detailed metrics)

### 4.2 Data Transformation Methods
- **Task**: Implement methods to transform API data into visualization-ready format
- **Details**:
  - Create a `DataFormatter` class with methods:
    - `format_for_bar_chart(data, x_key, y_key)`: Format data for bar charts
    - `format_for_line_chart(data, date_key, value_key)`: Format data for time series
    - `format_for_pie_chart(data, label_key, value_key)`: Format data for pie charts
    - `format_for_table(data, columns)`: Format data for tabular display

### 4.3 MCP Server Enhancements
- **Task**: Update MCP server to include visualization data
- **Details**:
  - Enhance tool responses to include:
    - Raw data (as before)
    - Visualization-ready data formats
    - Suggested visualization types
    - Chart titles and axis labels

### 4.4 Visualization Testing
- **Task**: Test visualization data with Claude Artifacts
- **Details**:
  - Create test scenarios for each visualization type
  - Verify Claude can properly render the data
  - Document successful visualization approaches
  - Create example prompts/tools that demonstrate visualization capabilities

## Implementation Timeline

1. **SQLite Database Implementation**: 3 days
   - Day 1: Schema design and DatabaseManager class
   - Day 2: Integration with Google Ads client
   - Day 3: Testing and refinement

2. **Unit Test Implementation**: 5 days
   - Day 1: Test framework setup and Google Ads client basic tests
   - Day 2: Complete Google Ads client tests
   - Day 3: MCP server tests
   - Day 4: Database manager tests
   - Day 5: Integration tests

3. **Google Ads API Integration Testing**: 3 days
   - Day 1: Environment setup and credentials
   - Day 2: Manual integration testing
   - Day 3: Claude Desktop testing

4. **Visualization Data Formatting**: 4 days
   - Day 1: Data structure analysis
   - Day 2: Data transformation methods
   - Day 3: MCP server enhancements
   - Day 4: Visualization testing with Claude

**Total Duration**: 15 working days

## Success Criteria

1. **SQLite Implementation**:
   - Database schema matches Backend Schema Document specifications
   - All Google Ads API responses are properly cached
   - Cache invalidation works as expected
   - Performance meets or exceeds the in-memory implementation

2. **Unit Tests**:
   - Test coverage exceeds 80% for all modules
   - All critical paths are covered by tests
   - Tests run successfully in the CI environment
   - Mocks and fixtures properly simulate real-world scenarios

3. **API Integration**:
   - Successful connection to Google Ads API
   - Correct data retrieval and formatting
   - Proper error handling for API failures
   - Claude Desktop successfully communicates with the server

4. **Visualization**:
   - Data is formatted correctly for visualization
   - Claude Artifacts can render the data without errors
   - Visualizations are informative and match user expectations
   - Multiple visualization types are supported

## References

1. Backend Schema Document (Section 3: Data Handling, Caching & Light DB Strategy)
2. Implementation Plan (Phases 2-5)
3. Google Ads API Python SDK Documentation
4. Claude Artifacts Documentation for Data Visualization

---

*This plan may be referenced using the shorthand "@SAGE-Plan" in future discussions.*
