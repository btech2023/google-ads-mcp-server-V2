# SAGE_VIZ_PRISM: Powerful Rendering & Interactive Structural Manifestation
**Date: 2025-03-17**

## Overview

The PRISM plan (Powerful Rendering & Interactive Structural Manifestation) focuses on completing and enhancing the visualization capabilities of the Google Ads KPI MCP Server. Building on the existing implementation, this plan addresses key gaps identified in the SAGE-Viz Assessment and introduces advanced visualization features to maximize the value of Google Ads data when presented through Claude Artifacts.

## 1. Core Implementation Completion

### 1.1 Time Series Formatting
- **Task**: Implement missing `_format_time_series` method in server.py
- **Details**:
  ```python
  def _format_time_series(kpi_data):
      """Format KPI data for time series visualization.
      
      Args:
          kpi_data: List of daily KPI data points.
          
      Returns:
          Dictionary with time series data formatted for visualization.
      """
      # Group by date
      dates = {}
      for item in kpi_data:
          date = item["date"]
          if date not in dates:
              dates[date] = {
                  "date": date,
                  "cost": 0,
                  "conversions": 0,
                  "clicks": 0,
                  "impressions": 0
              }
          
          # Aggregate metrics for this date
          dates[date]["cost"] += item["cost"]
          dates[date]["conversions"] += item["conversions"]
          dates[date]["clicks"] += item["clicks"]
          dates[date]["impressions"] += item["impressions"]
      
      # Convert to sorted list
      time_series = list(dates.values())
      time_series.sort(key=lambda x: x["date"])
      
      return {
          "title": "Daily Performance Metrics",
          "data": time_series,
          "labels": {
              "x": "Date",
              "y": "Value",
              "series": ["Cost", "Conversions", "Clicks", "Impressions"]
          }
      }
  ```
- **Timeframe**: 1 day

### 1.2 Fix Visualization Method References
- **Task**: Ensure all visualization methods are properly referenced in server.py
- **Details**:
  - Update call_tool handler to use the _format_time_series method correctly
  - Fix any `self` references that should be module-level functions
  - Verify proper data handling when visualization data is empty
- **Timeframe**: 1 day

## 2. Enhanced Visualization Types

### 2.1 Pie Chart Implementation
- **Task**: Add campaign type distribution pie chart
- **Details**:
  - Create `_format_pie_chart` method for campaign type distribution
  - Implement in both GoogleAdsClient and server.py
  - Ensure proper formatting for Claude Artifacts compatibility
- **Timeframe**: 2 days

### 2.2 Combination Chart Implementation
- **Task**: Create combination charts for related metrics
- **Details**:
  - Implement cost vs. conversion visualization
  - Develop CTR vs. CPC comparison charts
  - Create ROI visualization (cost vs. conversion value)
- **Timeframe**: 3 days

### 2.3 Heatmap Implementation
- **Task**: Add heatmap visualization for performance by day of week/hour
- **Details**:
  - Extend GoogleAdsClient to fetch hourly/daily performance data
  - Implement heatmap data formatter
  - Add to server response structure
- **Timeframe**: 3 days

## 3. Visualization Testing Framework

### 3.1 Visualization Test Suite
- **Task**: Create comprehensive visualization test suite
- **Details**:
  - Implement tests for each visualization data structure
  - Verify proper JSON formatting and structure
  - Test edge cases (zero data, extremely large values, etc.)
- **Timeframe**: 2 days

### 3.2 Claude Artifacts Rendering Tests
- **Task**: Develop tests for Claude Artifacts rendering
- **Details**:
  - Create test script that submits visualization data to Claude
  - Capture and analyze rendering results
  - Document any rendering inconsistencies or issues
- **Timeframe**: 2 days

### 3.3 Cross-Browser Compatibility Tests
- **Task**: Test visualization rendering across browsers/devices
- **Details**:
  - Create test matrix for different environments
  - Document any platform-specific rendering issues
  - Implement workarounds for problem areas
- **Timeframe**: 2 days

## 4. Visualization Documentation

### 4.1 Usage Documentation
- **Task**: Create comprehensive visualization usage documentation
- **Details**:
  - Document each visualization type with examples
  - Provide sample MCP requests and responses
  - Include screenshots of rendered visualizations
- **Timeframe**: 3 days

### 4.2 Example Query Library
- **Task**: Develop a library of example visualization queries
- **Details**:
  - Create example prompts for different visualization scenarios
  - Document recommended parameters for optimal visualizations
  - Include sample Claude prompts for interactive analysis
- **Timeframe**: 2 days

### 4.3 Interactive Documentation
- **Task**: Create interactive documentation with live examples
- **Details**:
  - Develop documentation that can trigger live visualizations
  - Include interactive parameter adjustment capability
  - Provide copy-paste examples for users
- **Timeframe**: 3 days

## 5. Performance Optimization

### 5.1 Data Reduction Strategies
- **Task**: Implement data reduction for large datasets
- **Details**:
  - Develop intelligent sampling for time series with many data points
  - Implement aggregation for daily/weekly/monthly views
  - Create progressive loading for large datasets
- **Timeframe**: 3 days

### 5.2 Caching Enhancement
- **Task**: Optimize caching specifically for visualization data
- **Details**:
  - Implement separate cache entries for different visualization types
  - Add cache versioning to handle visualization format changes
  - Optimize cache key generation for visualization-specific queries
- **Timeframe**: 2 days

### 5.3 Response Size Optimization
- **Task**: Optimize response payload size
- **Details**:
  - Implement numeric precision control to reduce JSON size
  - Add options for response compression
  - Create parameter to control visualization detail level
- **Timeframe**: 2 days

## Implementation Timeline

1. **Core Implementation Completion**: 2 days
   - Day 1-2: Implement missing methods and fix references

2. **Enhanced Visualization Types**: 8 days
   - Day 3-4: Pie chart implementation
   - Day 5-7: Combination chart implementation
   - Day 8-10: Heatmap implementation

3. **Visualization Testing Framework**: 6 days
   - Day 11-12: Visualization test suite
   - Day 13-14: Claude Artifacts rendering tests
   - Day 15-16: Cross-browser compatibility tests

4. **Visualization Documentation**: 8 days
   - Day 17-19: Usage documentation
   - Day 20-21: Example query library
   - Day 22-24: Interactive documentation

5. **Performance Optimization**: 7 days
   - Day 25-27: Data reduction strategies
   - Day 28-29: Caching enhancement
   - Day 30-31: Response size optimization

**Total Duration**: 31 working days (approximately 6-7 weeks)

## Success Criteria

1. **Functionality**:
   - All visualization methods are complete and working
   - At least 5 distinct visualization types are supported
   - Data structures are optimized for Claude Artifacts

2. **Performance**:
   - Visualization data preparation adds less than 100ms overhead
   - Response size increases by less than 30% with visualization data
   - Cache effectiveness remains above 80%

3. **Usability**:
   - Documentation includes examples for all visualization types
   - Users can create visualizations with minimal configuration
   - Visualization defaults provide immediate value

4. **Quality**:
   - Test coverage for visualization code exceeds 90%
   - Rendering success rate in Claude Artifacts exceeds 95%
   - No critical rendering issues across modern browsers

## References

1. SAGE-Viz Assessment (2025-03-17)
2. Claude Artifacts Visualization Documentation
3. Google Ads API Documentation
4. MCP Protocol Specification

---

*This plan may be referenced using the shorthand "@PRISM" in future discussions.*
