# SAGE-VIZ-PRISM-STELLAR
## Strategic Technological Enhancements for Latency, Load, and Advanced Rendering
**Date: 2025-03-17**

## Overview

Building on the successful implementation of the SAGE-VIZ-PRISM plan, this STELLAR enhancement initiative addresses advanced optimization, customization, and interactive documentation capabilities for the Google Ads KPI MCP Server visualization features. The STELLAR plan focuses on elevating the visualization system from excellent to extraordinary, with particular emphasis on performance, interactivity, and customization.

## 1. Performance Optimization Enhancements

### 1.1 Adaptive Data Sampling Engine
- **Task**: Implement an intelligent data sampling system for large time series datasets
- **Details**:
  ```python
  def adaptive_sample_time_series(time_series_data, target_points=100):
      """
      Intelligently sample time series data to a target number of points while preserving trends.
      
      For large datasets, this reduces payload size while maintaining visual fidelity.
      
      Args:
          time_series_data: Original time series data (list of data points)
          target_points: Desired number of points in the result
          
      Returns:
          Sampled data that preserves visual trends
      """
      # Implementation steps:
      # 1. If data is already smaller than target, return as-is
      if len(time_series_data) <= target_points:
          return time_series_data
          
      # 2. For larger datasets, use the Largest-Triangle-Three-Buckets algorithm
      # This algorithm preserves visual trends better than uniform sampling
      sampled_data = []
      
      # Divide data into buckets
      bucket_size = len(time_series_data) / target_points
      
      # Always include first point
      sampled_data.append(time_series_data[0])
      
      # Process each bucket to find the point that creates the largest triangle with neighbors
      for i in range(1, target_points - 1):
          # Calculate bucket boundaries
          bucket_start = int((i - 1) * bucket_size)
          bucket_end = int(i * bucket_size)
          next_bucket_end = int((i + 1) * bucket_size)
          
          # Find point in current bucket that creates largest triangle
          max_area = -1
          max_point = None
          
          for j in range(bucket_start, bucket_end):
              # Calculate triangle area with last sampled point and a point from next bucket
              area = calculate_triangle_area(
                  sampled_data[-1],
                  time_series_data[j],
                  # Use middle point of next bucket as reference
                  time_series_data[min(len(time_series_data) - 1, (bucket_end + next_bucket_end) // 2)]
              )
              
              if area > max_area:
                  max_area = area
                  max_point = time_series_data[j]
                  
          sampled_data.append(max_point)
      
      # Always include last point
      sampled_data.append(time_series_data[-1])
      
      return sampled_data
  
  def calculate_triangle_area(p1, p2, p3):
      """Calculate the area of a triangle formed by three data points."""
      # Extract x and y values (assuming x is date and y is a metric value)
      # For simplicity, convert dates to timestamp values
      x1 = datetime.strptime(p1["date"], "%Y-%m-%d").timestamp()
      y1 = p1["metric_value"]
      
      x2 = datetime.strptime(p2["date"], "%Y-%m-%d").timestamp()
      y2 = p2["metric_value"]
      
      x3 = datetime.strptime(p3["date"], "%Y-%m-%d").timestamp()
      y3 = p3["metric_value"]
      
      # Calculate area using the cross product
      return abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2)
  ```
- **Integration**:
  - Modify `_format_time_series` to use adaptive sampling for datasets larger than 100 points
  - Add a `sampling_threshold` parameter to control when sampling is applied
  - Add sampling metadata to the visualization output to indicate when sampling occurred
- **Timeframe**: 3 days

### 1.2 Multi-Level Temporal Aggregation
- **Task**: Implement automatic time-based aggregation for different date ranges
- **Details**:
  ```python
  def auto_aggregate_time_series(time_series_data, date_range):
      """
      Automatically determine and apply the appropriate time aggregation level.
      
      Args:
          time_series_data: Daily time series data
          date_range: Dictionary with 'start_date' and 'end_date'
          
      Returns:
          Aggregated time series and aggregation level used
      """
      start = datetime.strptime(date_range["start_date"], "%Y-%m-%d")
      end = datetime.strptime(date_range["end_date"], "%Y-%m-%d")
      days_difference = (end - start).days
      
      # Determine aggregation level based on date range
      if days_difference > 365:
          # For more than a year, aggregate by month
          return aggregate_by_month(time_series_data), "monthly"
      elif days_difference > 90:
          # For more than 3 months, aggregate by week
          return aggregate_by_week(time_series_data), "weekly"
      else:
          # For shorter periods, use daily data
          return time_series_data, "daily"
          
  def aggregate_by_week(time_series_data):
      """Aggregate daily data to weekly data."""
      # Group by ISO week
      weekly_data = {}
      
      for item in time_series_data:
          date_obj = datetime.strptime(item["date"], "%Y-%m-%d")
          year, week, _ = date_obj.isocalendar()
          week_key = f"{year}-W{week:02d}"
          
          if week_key not in weekly_data:
              weekly_data[week_key] = {
                  "date": week_key,
                  "week_start": date_obj - timedelta(days=date_obj.weekday()),
                  "cost": 0,
                  "conversions": 0,
                  "clicks": 0,
                  "impressions": 0
              }
          
          # Aggregate metrics
          weekly_data[week_key]["cost"] += item.get("cost", 0)
          weekly_data[week_key]["conversions"] += item.get("conversions", 0)
          weekly_data[week_key]["clicks"] += item.get("clicks", 0)
          weekly_data[week_key]["impressions"] += item.get("impressions", 0)
      
      # Convert to list and format dates for display
      result = []
      for key, data in sorted(weekly_data.items()):
          week_start = data["week_start"].strftime("%Y-%m-%d")
          week_end = (data["week_start"] + timedelta(days=6)).strftime("%Y-%m-%d")
          
          result.append({
              "date": f"{week_start} to {week_end}",
              "cost": data["cost"],
              "conversions": data["conversions"],
              "clicks": data["clicks"],
              "impressions": data["impressions"]
          })
      
      return result
  
  def aggregate_by_month(time_series_data):
      """Aggregate daily data to monthly data."""
      # Similar implementation as aggregate_by_week but for months
      monthly_data = {}
      
      for item in time_series_data:
          date_obj = datetime.strptime(item["date"], "%Y-%m-%d")
          month_key = date_obj.strftime("%Y-%m")
          
          if month_key not in monthly_data:
              monthly_data[month_key] = {
                  "date": month_key,
                  "month_name": date_obj.strftime("%B %Y"),
                  "cost": 0,
                  "conversions": 0,
                  "clicks": 0,
                  "impressions": 0
              }
          
          # Aggregate metrics
          monthly_data[month_key]["cost"] += item.get("cost", 0)
          monthly_data[month_key]["conversions"] += item.get("conversions", 0)
          monthly_data[month_key]["clicks"] += item.get("clicks", 0)
          monthly_data[month_key]["impressions"] += item.get("impressions", 0)
      
      # Convert to list with formatted month names
      result = []
      for key, data in sorted(monthly_data.items()):
          result.append({
              "date": data["month_name"],
              "cost": data["cost"],
              "conversions": data["conversions"],
              "clicks": data["clicks"],
              "impressions": data["impressions"]
          })
      
      return result
  ```
- **Integration**:
  - Update `_format_time_series` to use auto-aggregation based on date range
  - Add an optional `aggregation` parameter to allow manual control
  - Add aggregation metadata to visualization output
- **Timeframe**: 4 days

### 1.3 Progressive Loading Protocol
- **Task**: Implement a protocol for progressive loading of large datasets
- **Details**:
  - Create a mechanism to load large datasets in chunks
  - Initial response includes summary data and first chunk
  - Subsequent chunks can be requested as needed
  ```python
  def create_chunked_visualization(data, chunk_size=50):
      """
      Prepare a large dataset for progressive loading by chunking it.
      
      Args:
          data: Complete dataset
          chunk_size: Number of data points per chunk
          
      Returns:
          Dictionary with chunk metadata and first chunk
      """
      total_items = len(data)
      total_chunks = (total_items + chunk_size - 1) // chunk_size
      
      chunks = []
      for i in range(0, total_items, chunk_size):
          chunk = {
              "chunk_index": i // chunk_size,
              "start_index": i,
              "end_index": min(i + chunk_size, total_items),
              "data": data[i:i + chunk_size]
          }
          chunks.append(chunk)
      
      return {
          "total_items": total_items,
          "total_chunks": total_chunks,
          "chunk_size": chunk_size,
          "first_chunk": chunks[0],
          "chunk_uri_template": "google-ads://kpi/{cache_key}/chunk/{chunk_index}"
      }
  ```
- **Add endpoints for retrieving chunks**:
  ```python
  @server.read_resource()
  async def handle_read_resource(uri: AnyUrl) -> str:
      """
      Read a resource by URI, including chunked data resources.
      """
      if uri.scheme != "google-ads":
          raise ValueError(f"Unsupported URI scheme: {uri.scheme}")
      
      parts = uri.path.strip("/").split("/")
      
      # Handle normal KPI resources
      if parts[0] == "kpi" and len(parts) == 2:
          cache_key = parts[1]
          return json.dumps(google_ads_client.get_cached_kpi_data(cache_key))
      
      # Handle chunked data resources
      if parts[0] == "kpi" and len(parts) == 4 and parts[2] == "chunk":
          cache_key = parts[1]
          try:
              chunk_index = int(parts[3])
              
              # Get the full data
              data = google_ads_client.get_cached_kpi_data(cache_key)
              
              # Extract the visualization data that needs chunking
              if "visualization" in data and "time_series" in data["visualization"]:
                  time_series = data["visualization"]["time_series"]
                  
                  if "data" in time_series:
                      full_data = time_series["data"]
                      chunk_size = 50  # Should match the chunk size used in create_chunked_visualization
                      
                      start_index = chunk_index * chunk_size
                      end_index = min(start_index + chunk_size, len(full_data))
                      
                      if 0 <= start_index < len(full_data):
                          return json.dumps({
                              "chunk_index": chunk_index,
                              "start_index": start_index,
                              "end_index": end_index,
                              "data": full_data[start_index:end_index]
                          })
              
              raise ValueError(f"Invalid chunk index: {chunk_index}")
          except (ValueError, IndexError):
              raise ValueError(f"Invalid chunk index: {parts[3]}")
      
      raise ValueError(f"Resource not found: {uri}")
  ```
- **Update visualization output**:
  - Modify visualization methods to use chunking for large datasets
  - Add chunking metadata to visualization output
  - Provide client-side instructions for progressive loading
- **Timeframe**: 5 days

### 1.4 Visualization-Specific Caching
- **Task**: Implement specialized caching for visualization data
- **Details**:
  - Create separate cache entries for different visualization types
  - Add cache versioning to handle format changes
  - Implement TTL-based cache invalidation for visualizations
  ```python
  def create_visualization_cache_key(base_key, visualization_type, version="1"):
      """
      Create a cache key for a specific visualization type.
      
      Args:
          base_key: Base cache key for the dataset
          visualization_type: Type of visualization (e.g., "time_series", "pie_chart")
          version: Version of the visualization format
          
      Returns:
          Visualization-specific cache key
      """
      return f"{base_key}:viz:{visualization_type}:v{version}"
  
  def cache_visualization_data(db_manager, base_key, visualization_type, data, ttl_minutes=60):
      """
      Cache visualization-specific data with TTL.
      
      Args:
          db_manager: Database manager instance
          base_key: Base cache key for the dataset
          visualization_type: Type of visualization
          data: Visualization data to cache
          ttl_minutes: Time-to-live in minutes
          
      Returns:
          Cache key used
      """
      viz_key = create_visualization_cache_key(base_key, visualization_type)
      
      # Prepare cache entry
      cache_data = {
          "data": data,
          "created_at": datetime.now().isoformat(),
          "expires_at": (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat(),
          "version": "1"  # Current visualization format version
      }
      
      # Store in database
      db_manager.store_visualization_data(viz_key, json.dumps(cache_data))
      
      return viz_key
  
  def get_cached_visualization(db_manager, base_key, visualization_type):
      """
      Retrieve cached visualization data if available and not expired.
      
      Args:
          db_manager: Database manager instance
          base_key: Base cache key for the dataset
          visualization_type: Type of visualization
          
      Returns:
          Cached visualization data or None if not found or expired
      """
      viz_key = create_visualization_cache_key(base_key, visualization_type)
      
      # Get from cache
      cached = db_manager.get_visualization_data(viz_key)
      if not cached:
          return None
      
      # Parse the cached data
      try:
          cache_data = json.loads(cached)
          
          # Check if expired
          expires_at = datetime.fromisoformat(cache_data["expires_at"])
          if datetime.now() > expires_at:
              return None
          
          return cache_data["data"]
      except (json.JSONDecodeError, KeyError, ValueError):
          return None
  ```
- **Database Schema Updates**:
  ```sql
  CREATE TABLE IF NOT EXISTS visualization_cache (
      cache_key TEXT PRIMARY KEY,
      visualization_data TEXT NOT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      expires_at TIMESTAMP NOT NULL
  );
  
  CREATE INDEX IF NOT EXISTS idx_visualization_cache_expires
  ON visualization_cache(expires_at);
  ```
- **Integration**:
  - Add methods to `DatabaseManager` for visualization caching
  - Update visualization formatting methods to use the cache
  - Implement cache cleanup for expired entries
- **Timeframe**: 4 days

### 1.5 Response Size Optimization
- **Task**: Implement techniques to reduce response payload size
- **Details**:
  - Add numeric precision control
  - Implement optional gzip compression
  - Create response size estimation
  ```python
  def optimize_numeric_precision(data, precision=2):
      """
      Optimize numeric precision in visualization data.
      
      Args:
          data: Visualization data (dict or list)
          precision: Number of decimal places to keep
          
      Returns:
          Data with optimized numeric precision
      """
      if isinstance(data, dict):
          result = {}
          for key, value in data.items():
              if isinstance(value, float):
                  result[key] = round(value, precision)
              elif isinstance(value, (dict, list)):
                  result[key] = optimize_numeric_precision(value, precision)
              else:
                  result[key] = value
          return result
      elif isinstance(data, list):
          return [optimize_numeric_precision(item, precision) for item in data]
      else:
          return data
  
  def estimate_response_size(data):
      """
      Estimate the size of a response payload.
      
      Args:
          data: Response data
          
      Returns:
          Estimated size in bytes
      """
      return len(json.dumps(data).encode('utf-8'))
  
  def compress_response(data):
      """
      Compress response data using gzip.
      
      Args:
          data: Response data
          
      Returns:
          Gzip-compressed data as base64 string
      """
      import gzip
      import base64
      
      # Convert to JSON
      json_data = json.dumps(data).encode('utf-8')
      
      # Compress
      compressed = gzip.compress(json_data)
      
      # Convert to base64 for safe transport
      return base64.b64encode(compressed).decode('utf-8')
  ```
- **Integration**:
  - Add compression flags to API responses
  - Update server handlers to optionally compress large responses
  - Implement size estimation for response monitoring
- **Timeframe**: 3 days

## 2. Interactive Documentation System

### 2.1 Interactive Documentation Framework
- **Task**: Create a web-based interactive documentation system
- **Details**:
  - Develop a simple React application for interactive docs
  - Implement live visualization examples
  - Allow parameter adjustment with real-time updates
  ```jsx
  // Example React component for interactive documentation
  import React, { useState } from 'react';
  import { LineChart, BarChart, PieChart, ComboChart, HeatMap } from './charts';
  
  const VisualizationDemo = () => {
    const [chartType, setChartType] = useState('line');
    const [dataSize, setDataSize] = useState('small');
    const [aggregation, setAggregation] = useState('daily');
    
    // Sample data (would be loaded from examples)
    const sampleData = getSampleData(chartType, dataSize, aggregation);
    
    return (
      <div className="visualization-demo">
        <div className="controls">
          <div className="control-group">
            <label>Chart Type:</label>
            <select value={chartType} onChange={e => setChartType(e.target.value)}>
              <option value="line">Line Chart</option>
              <option value="bar">Bar Chart</option>
              <option value="pie">Pie Chart</option>
              <option value="combo">Combination Chart</option>
              <option value="heatmap">Heat Map</option>
            </select>
          </div>
          
          <div className="control-group">
            <label>Data Size:</label>
            <select value={dataSize} onChange={e => setDataSize(e.target.value)}>
              <option value="small">Small (10 points)</option>
              <option value="medium">Medium (50 points)</option>
              <option value="large">Large (200 points)</option>
            </select>
          </div>
          
          <div className="control-group">
            <label>Aggregation:</label>
            <select value={aggregation} onChange={e => setAggregation(e.target.value)}>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
        </div>
        
        <div className="visualization-container">
          {chartType === 'line' && <LineChart data={sampleData} />}
          {chartType === 'bar' && <BarChart data={sampleData} />}
          {chartType === 'pie' && <PieChart data={sampleData} />}
          {chartType === 'combo' && <ComboChart data={sampleData} />}
          {chartType === 'heatmap' && <HeatMap data={sampleData} />}
        </div>
        
        <div className="code-preview">
          <h3>Claude Artifact Code:</h3>
          <pre>
            {generateClaudeArtifactCode(chartType, sampleData)}
          </pre>
        </div>
      </div>
    );
  };
  
  function getSampleData(chartType, dataSize, aggregation) {
    // Return appropriate sample data based on parameters
  }
  
  function generateClaudeArtifactCode(chartType, data) {
    // Generate the Claude artifact code for the current visualization
    const artifactType = chartType === 'combo' ? 'combo' : 
                         chartType === 'heatmap' ? 'heatmap' : 
                         chartType;
    
    return `<chart type="${artifactType}">
  ${JSON.stringify(data, null, 2)}
</chart>`;
  }
  ```
- **Static Documentation Site**:
  - Create a simple static site using a framework like Next.js or Gatsby
  - Host on GitHub Pages or similar platform
  - Include live examples with React components
- **Timeframe**: 8 days

### 2.2 Example Library
- **Task**: Create a comprehensive library of visualization examples
- **Details**:
  - Develop examples for each visualization type
  - Include sample data for different scenarios
  - Document chart configuration options
  ```javascript
  // Example library structure
  const examples = {
    "time_series": [
      {
        "name": "Basic Time Series",
        "description": "Simple line chart showing cost over time",
        "data": { /* sample data */ },
        "code": `<chart type="line">...</chart>`
      },
      {
        "name": "Multi-Metric Time Series",
        "description": "Line chart showing multiple metrics over time",
        "data": { /* sample data */ },
        "code": `<chart type="line">...</chart>`
      },
      // More examples...
    ],
    "bar_charts": [
      // Bar chart examples
    ],
    "pie_charts": [
      // Pie chart examples
    ],
    "combo_charts": [
      // Combination chart examples
    ],
    "heatmaps": [
      // Heatmap examples
    ]
  };
  ```
- **Example Data Generation**:
  - Create realistic sample data for different Google Ads scenarios
  - Include edge cases and special situations
  - Generate data with different aggregation levels
- **Integration**:
  - Make examples accessible via the interactive documentation
  - Provide downloadable JSON samples
  - Include copy-paste-ready Claude artifact code
- **Timeframe**: 6 days

### 2.3 API Integration Playground
- **Task**: Create an interactive API playground for testing visualizations
- **Details**:
  - Develop a web interface for making MCP requests
  - Allow customization of request parameters
  - Render the resulting visualizations
  ```jsx
  import React, { useState } from 'react';
  import { LineChart, BarChart, PieChart } from './charts';
  
  const APIPlayground = () => {
    const [customerID, setCustomerID] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [segmentation, setSegmentation] = useState(['campaign']);
    const [response, setResponse] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    const handleSubmit = async (e) => {
      e.preventDefault();
      setLoading(true);
      setError(null);
      
      try {
        // This would be replaced with actual MCP client code
        const result = await mockMCPRequest({
          customer_id: customerID,
          start_date: startDate,
          end_date: endDate,
          segmentation: segmentation
        });
        
        setResponse(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    return (
      <div className="api-playground">
        <h2>Google Ads KPI API Playground</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Customer ID:</label>
            <input 
              type="text" 
              value={customerID} 
              onChange={e => setCustomerID(e.target.value)}
              placeholder="e.g., 1234567890"
            />
          </div>
          
          <div className="form-group">
            <label>Start Date:</label>
            <input 
              type="date" 
              value={startDate} 
              onChange={e => setStartDate(e.target.value)}
            />
          </div>
          
          <div className="form-group">
            <label>End Date:</label>
            <input 
              type="date" 
              value={endDate} 
              onChange={e => setEndDate(e.target.value)}
            />
          </div>
          
          <div className="form-group">
            <label>Segmentation:</label>
            <div className="checkbox-group">
              <label>
                <input 
                  type="checkbox" 
                  checked={segmentation.includes('campaign')}
                  onChange={e => {
                    if (e.target.checked) {
                      setSegmentation([...segmentation, 'campaign']);
                    } else {
                      setSegmentation(segmentation.filter(s => s !== 'campaign'));
                    }
                  }}
                />
                Campaign
              </label>
              
              <label>
                <input 
                  type="checkbox" 
                  checked={segmentation.includes('ad_group')}
                  onChange={e => {
                    if (e.target.checked) {
                      setSegmentation([...segmentation, 'ad_group']);
                    } else {
                      setSegmentation(segmentation.filter(s => s !== 'ad_group'));
                    }
                  }}
                />
                Ad Group
              </label>
              
              <label>
                <input 
                  type="checkbox" 
                  checked={segmentation.includes('device')}
                  onChange={e => {
                    if (e.target.checked) {
                      setSegmentation([...segmentation, 'device']);
                    } else {
                      setSegmentation(segmentation.filter(s => s !== 'device'));
                    }
                  }}
                />
                Device
              </label>
            </div>
          </div>
          
          <button type="submit" disabled={loading}>
            {loading ? 'Loading...' : 'Run Query'}
          </button>
        </form>
        
        {error && (
          <div className="error-message">
            Error: {error}
          </div>
        )}
        
        {response && (
          <div className="results">
            <h3>API Response:</h3>
            
            <div className="tabs">
              <button className="tab-button active">Visualizations</button>
              <button className="tab-button">JSON Response</button>
              <button className="tab-button">Claude Artifacts</button>
            </div>
            
            <div className="tab-content">
              {/* Visualization tab */}
              <div className="visualizations">
                {response.visualization.time_series && (
                  <div className="chart-container">
                    <h4>Time Series Chart</h4>
                    <LineChart data={response.visualization.time_series.data} />
                  </div>
                )}
                
                {response.visualization.campaign_type_distribution && (
                  <div className="chart-container">
                    <h4>Campaign Type Distribution</h4>
                    <PieChart data={response.visualization.campaign_type_distribution.data} />
                  </div>
                )}
                
                {/* Additional charts would be added here */}
              </div>
              
              {/* JSON Response tab (hidden initially) */}
              <div className="json-response" style={{display: 'none'}}>
                <pre>
                  {JSON.stringify(response, null, 2)}
                </pre>
              </div>
              
              {/* Claude Artifacts tab (hidden initially) */}
              <div className="claude-artifacts" style={{display: 'none'}}>
                <div className="artifact">
                  <h4>Time Series Chart</h4>
                  <pre>
                    {`<chart type="line">
${JSON.stringify(response.visualization.time_series, null, 2)}
</chart>`}
                  </pre>
                  <button className="copy-button">Copy to Clipboard</button>
                </div>
                
                {/* Additional artifacts would be added here */}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };
  
  // Mock MCP request for demo purposes
  async function mockMCPRequest(params) {
    // In a real implementation, this would call the actual MCP client
    // For the playground, we'll return sample data
    return getSampleResponseData(params);
  }
  
  function getSampleResponseData(params) {
    // Return sample data based on the request parameters
  }
  ```
- **Integration**:
  - Create a mock MCP client for the playground
  - Add sample response data for different query parameters
  - Include visualization rendering for all chart types
- **Timeframe**: 7 days

## 3. Advanced Chart Customization

### 3.1 Theme and Style System
- **Task**: Implement a theming and styling system for visualizations
- **Details**:
  - Create a theme specification for charts
  - Support light and dark modes
  - Allow custom color palettes
  ```python
  def apply_chart_theme(visualization_data, theme=None, color_palette=None):
      """
      Apply a theme to visualization data.
      
      Args:
          visualization_data: Original visualization data
          theme: Theme name ('light', 'dark', 'brand') or theme object
          color_palette: Optional custom color palette
          
      Returns:
          Visualization data with theme applied
      """
      # Get the theme configuration
      theme_config = get_theme_config(theme)
      
      # Override with custom color palette if provided
      if color_palette:
          theme_config["colors"] = color_palette
      
      # Create a copy of the visualization data
      themed_data = copy.deepcopy(visualization_data)
      
      # Apply theme settings
      if "chartType" in themed_data:
          chart_type = themed_data["chartType"]
          
          # Add theme properties based on chart type
          if chart_type in ["line", "bar", "combination"]:
              themed_data["theme"] = {
                  "colors": theme_config["colors"],
                  "backgroundColor": theme_config["backgroundColor"],
                  "gridColor": theme_config["gridColor"],
                  "textColor": theme_config["textColor"],
                  "fontFamily": theme_config["fontFamily"]
              }
          elif chart_type == "pie":
              themed_data["theme"] = {
                  "colors": theme_config["colors"],
                  "backgroundColor": theme_config["backgroundColor"],
                  "textColor": theme_config["textColor"],
                  "fontFamily": theme_config["fontFamily"]
              }
          elif chart_type == "heatmap":
              themed_data["theme"] = {
                  "colorRange": theme_config["heatmapColors"],
                  "backgroundColor": theme_config["backgroundColor"],
                  "textColor": theme_config["textColor"],
                  "fontFamily": theme_config["fontFamily"]
              }
      
      return themed_data
  
  def get_theme_config(theme_name):
      """Get the configuration for a named theme."""
      themes = {
          "light": {
              "backgroundColor": "#ffffff",
              "textColor": "#333333",
              "gridColor": "#e0e0e0",
              "fontFamily": "Arial, sans-serif",
              "colors": ["#4285F4", "#EA4335", "#FBBC05", "#34A853", "#5E35B1", "#00ACC1", "#F57C00", "#8D6E63"],
              "heatmapColors": ["#deebf7", "#9ecae1", "#3182bd"]
          },
          "dark": {
              "backgroundColor": "#1e1e1e",
              "textColor": "#e0e0e0",
              "gridColor": "#333333",
              "fontFamily": "Arial, sans-serif",
              "colors": ["#8ab4f8", "#f28b82", "#fdd663", "#81c995", "#b4a7f5", "#78d9ec", "#ffa657", "#d7b5ac"],
              "heatmapColors": ["#0d3559", "#2171b5", "#6baed6"]
          },
          "brand": {
              "backgroundColor": "#f5f5f5",
              "textColor": "#202124",
              "gridColor": "#dadce0",
              "fontFamily": "Google Sans, Arial, sans-serif",
              "colors": ["#1a73e8", "#ea4335", "#fbbc04", "#34a853", "#5f6368", "#4285f4", "#ee675c", "#fcc934"],
              "heatmapColors": ["#d1e5f5", "#73b3d8", "#0a5caa"]
          }
      }
      
      return themes.get(theme_name, themes["light"])
  ```
- **Integration**:
  - Add theme parameter to visualization APIs
  - Update documentation with theming examples
  - Create theme preview in the interactive documentation
- **Timeframe**: 5 days

### 3.2 Chart Configuration System
- **Task**: Implement a comprehensive chart configuration system
- **Details**:
  - Allow customization of axes, legends, tooltips, etc.
  - Support advanced chart features
  - Create a consistent configuration API
  ```python
  def configure_chart(visualization_data, config=None):
      """
      Apply advanced configuration to a chart.
      
      Args:
          visualization_data: Original visualization data
          config: Chart configuration options
          
      Returns:
          Visualization data with configuration applied
      """
      if not config:
          return visualization_data
      
      # Create a copy of the visualization data
      configured_data = copy.deepcopy(visualization_data)
      
      # Apply configuration by chart type
      chart_type = configured_data.get("chartType")
      
      if chart_type in ["line", "bar", "combination"]:
          # Configure axes
          if "xAxis" in config:
              configured_data["xAxis"] = {
                  **(configured_data.get("xAxis", {})),
                  **config["xAxis"]
              }
          
          if "yAxis" in config:
              configured_data["yAxis"] = {
                  **(configured_data.get("yAxis", {})),
                  **config["yAxis"]
              }
          
          # Configure legend
          if "legend" in config:
              configured_data["legend"] = config["legend"]
          
          # Configure tooltip
          if "tooltip" in config:
              configured_data["tooltip"] = config["tooltip"]
          
          # Configure animation
          if "animation" in config:
              configured_data["animation"] = config["animation"]
      
      elif chart_type == "pie":
          # Configure legend
          if "legend" in config:
              configured_data["legend"] = config["legend"]
          
          # Configure label display
          if "labels" in config:
              configured_data["labels"] = config["labels"]
          
          # Configure donut mode
          if "innerRadius" in config:
              configured_data["innerRadius"] = config["innerRadius"]
      
      elif chart_type == "heatmap":
          # Configure axes
          if "xAxis" in config:
              configured_data["xAxis"] = {
                  **(configured_data.get("xAxis", {})),
                  **config["xAxis"]
              }
          
          if "yAxis" in config:
              configured_data["yAxis"] = {
                  **(configured_data.get("yAxis", {})),
                  **config["yAxis"]
              }
          
          # Configure cell appearance
          if "cell" in config:
              configured_data["cell"] = config["cell"]
      
      return configured_data
  ```
- **Configuration Options**:
  - Create a comprehensive set of configuration options for each chart type
  - Document defaults and available options
  - Provide examples of common configurations
- **Integration**:
  - Add configuration parameter to visualization APIs
  - Update documentation with configuration examples
  - Add configuration controls to the interactive playground
- **Timeframe**: 6 days

### 3.3 Annotation and Reference Line System
- **Task**: Implement annotations and reference lines for charts
- **Details**:
  - Allow adding annotations to specific data points
  - Support horizontal and vertical reference lines
  - Create custom labels and markers
  ```python
  def add_chart_annotations(visualization_data, annotations=None, reference_lines=None):
      """
      Add annotations and reference lines to a chart.
      
      Args:
          visualization_data: Original visualization data
          annotations: List of annotation objects
          reference_lines: List of reference line objects
          
      Returns:
          Visualization data with annotations and reference lines
      """
      if not annotations and not reference_lines:
          return visualization_data
      
      # Create a copy of the visualization data
      annotated_data = copy.deepcopy(visualization_data)
      
      # Add annotations if provided
      if annotations:
          annotated_data["annotations"] = annotations
      
      # Add reference lines if provided
      if reference_lines:
          annotated_data["referenceLines"] = reference_lines
      
      return annotated_data
  
  def create_data_point_annotation(data_index, label, description=None, style=None):
      """
      Create an annotation for a specific data point.
      
      Args:
          data_index: Index of the data point to annotate
          label: Short label for the annotation
          description: Optional longer description
          style: Optional styling for the annotation
          
      Returns:
          Annotation object
      """
      annotation = {
          "type": "dataPoint",
          "dataIndex": data_index,
          "label": label
      }
      
      if description:
          annotation["description"] = description
      
      if style:
          annotation["style"] = style
      
      return annotation
  
  def create_reference_line(value, axis="y", label=None, style=None):
      """
      Create a reference line for a chart.
      
      Args:
          value: Value where the line should be placed
          axis: Which axis the line corresponds to ('x' or 'y')
          label: Optional label for the line
          style: Optional styling for the line
          
      Returns:
          Reference line object
      """
      reference_line = {
          "axis": axis,
          "value": value
      }
      
      if label:
          reference_line["label"] = label
      
      if style:
          reference_line["style"] = style
      
      return reference_line
  ```
- **Example Usage**:
  ```python
  # Add a milestone annotation to a time series chart
  time_series_data = _format_time_series(kpi_data)
  
  # Find the index of a specific date
  milestone_date = "2023-03-15"
  milestone_index = next((i for i, d in enumerate(time_series_data["data"]) 
                         if d["name"] == milestone_date), None)
  
  if milestone_index is not None:
      # Add annotation for campaign launch
      time_series_data = add_chart_annotations(
          time_series_data,
          annotations=[
              create_data_point_annotation(
                  milestone_index,
                  "Campaign Launch",
                  "New brand campaign launched",
                  {"color": "#34A853", "markerSize": 8}
              )
          ],
          reference_lines=[
              create_reference_line(
                  avg_cost,
                  axis="y",
                  label="Avg. Cost",
                  {"strokeColor": "#EA4335", "strokeWidth": 2, "strokeDashArray": [3, 3]}
              )
          ]
      )
  ```
- **Integration**:
  - Add annotation methods to the server
  - Update visualization methods to support annotations
  - Add annotation examples to documentation
- **Timeframe**: 5 days

### 3.4 Export and Embedding System
- **Task**: Implement export and embedding options for visualizations
- **Details**:
  - Allow exporting charts as images
  - Support embedding charts in other applications
  - Create shareable links for visualizations
  ```javascript
  // Client-side export utilities
  function exportChartAsImage(chartElement, filename = 'chart.png') {
    // Use html2canvas or similar library
    import('html2canvas').then(html2canvas => {
      html2canvas.default(chartElement).then(canvas => {
        const link = document.createElement('a');
        link.download = filename;
        link.href = canvas.toDataURL('image/png');
        link.click();
      });
    });
  }
  
  function getEmbedCode(chartData, width = 600, height = 400) {
    const chartJson = JSON.stringify(chartData);
    
    return `
  <iframe
    src="https://your-domain.com/embed-chart?data=${encodeURIComponent(chartJson)}"
    width="${width}"
    height="${height}"
    frameborder="0"
    allow="fullscreen"
  ></iframe>
    `.trim();
  }
  
  function getShareableLink(chartData) {
    // Generate a unique ID for the chart data
    const chartId = generateUniqueId();
    
    // Store chart data in database or temporary storage
    saveChartData(chartId, chartData);
    
    return `https://your-domain.com/shared-chart/${chartId}`;
  }
  ```
- **Server-Side Components**:
  - Create endpoints for storing and retrieving shared charts
  - Implement temporary storage for shared chart data
  - Add authentication for private charts
- **Integration**:
  - Add export buttons to the interactive documentation
  - Create an embed page for iframe embedding
  - Add sharing functionality to the playground
- **Timeframe**: 6 days

## Implementation Timeline

1. **Performance Optimization Enhancements**: 19 days
   - Day 1-3: Adaptive Data Sampling Engine
   - Day 4-7: Multi-Level Temporal Aggregation
   - Day 8-12: Progressive Loading Protocol
   - Day 13-16: Visualization-Specific Caching
   - Day 17-19: Response Size Optimization

2. **Interactive Documentation System**: 21 days
   - Day 20-27: Interactive Documentation Framework
   - Day 28-33: Example Library
   - Day 34-40: API Integration Playground

3. **Advanced Chart Customization**: 22 days
   - Day 41-45: Theme and Style System
   - Day 46-51: Chart Configuration System
   - Day 52-56: Annotation and Reference Line System
   - Day 57-62: Export and Embedding System

**Total Duration**: 62 working days (approximately 12-13 weeks)

## Success Criteria

1. **Performance Metrics**:
   - 90% reduction in payload size for datasets > 1000 points
   - Cache hit rate > 95% for visualization data
   - Response time for large datasets < 500ms
   - Memory usage stays within acceptable limits

2. **Documentation Quality**:
   - 100% of visualization types have interactive examples
   - Documentation covers all configuration options
   - User feedback rating > 4.5/5 for documentation quality
   - 90% success rate for first-time users following examples

3. **Visualization Enhancements**:
   - Support for all advanced customization options
   - Theme system compatible with all chart types
   - Annotation system works with all time-based charts
   - Export functionality works in major browsers

## References

1. SAGE-VIZ-PRISM Plan (2025-03-17)
2. Cursor PRISM Implementation Assessment (2025-03-17)
3. Google Ads API Documentation
4. Claude Artifacts Visualization Documentation
5. Chart.js and Recharts Documentation
6. React Documentation for Interactive Components

---

*This plan may be referenced using the shorthand "@STELLAR" in future discussions.*
