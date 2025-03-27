# Google Ads MCP Server Monitoring Guide

This directory contains the monitoring and alerting configuration for the Google Ads MCP Server.

## Monitoring Components

Our monitoring system consists of:

1. **Metrics Collection**: Prometheus metrics exposed by the application and collected by Google Cloud Monitoring
2. **Custom Dashboard**: Pre-configured dashboard for visualizing key performance indicators
3. **Alerting Policies**: Automated alerts for potential issues

## Setting Up Monitoring

### Prerequisites

- Google Cloud SDK (`gcloud`) installed and configured
- Permissions to create/modify dashboards and alerting policies
- A notification channel ID (for alerts)

### Installation

1. Run the setup script with your project ID:

```bash
chmod +x apply-monitoring.sh
./apply-monitoring.sh YOUR_PROJECT_ID [NOTIFICATION_CHANNEL_ID]
```

If you don't provide a notification channel ID, the dashboard will be created, but alerting policies will be skipped.

### Creating a Notification Channel

To create a notification channel for alerts:

1. Go to [Monitoring > Alerting > Notification channels](https://console.cloud.google.com/monitoring/alerting/notifications)
2. Click "Add New"
3. Choose your notification type (Email, Slack, PagerDuty, etc.)
4. Follow the prompts to set up the channel
5. Once created, you can get the channel ID with:

```bash
gcloud alpha monitoring channels list --project=YOUR_PROJECT_ID
```

## Dashboard Overview

The dashboard provides visibility into several key areas:

### HTTP Performance
- **Request Count**: Total HTTP requests by status code
- **Latency**: P95 response time for HTTP requests

### Google Ads API
- **Request Count**: Total API calls by endpoint and status
- **Latency**: P95 response time for API calls by endpoint

### MCP Tool Performance
- **Request Count**: Total MCP tool calls by tool name and status
- **Latency**: P95 response time for MCP tool operations by tool name

### Error Analysis
- **Error Rate Breakdown**: Comparison of HTTP, Google Ads API, and MCP tool errors

### System Resources
- **Memory Usage**: Current and limit memory usage
- **CPU Usage**: CPU utilization over time
- **Network Traffic**: Ingress and egress network traffic
- **Filesystem Usage**: Storage usage and limits

### Application Health
- **Cache Performance**: Cache hit/miss rates
- **Health Check Status**: Overall application health status
- **Pod Restarts**: Container restart events

## Alerting Policies

The following alerts are configured:

1. **High API Latency**: Triggers when P95 latency exceeds 1 second for 5 minutes
2. **High HTTP Error Rate**: Triggers when error rate exceeds 5% for 5 minutes
3. **Google Ads API Errors**: Triggers when API error rate exceeds 2% for 5 minutes
4. **High Memory Usage**: Triggers when memory usage exceeds 80% of limit for 5 minutes
5. **High CPU Usage**: Triggers when CPU usage exceeds 80% of limit for 5 minutes
6. **Health Check Failure**: Triggers when application health check fails
7. **Pod Restarts**: Triggers when pods restart unexpectedly
8. **MCP Tool Errors**: Triggers when MCP tool error rate exceeds 3% for 5 minutes
9. **High MCP Tool Latency**: Triggers when P95 MCP tool latency exceeds 3 seconds for 5 minutes
10. **Low Cache Hit Rate**: Triggers when cache hit rate falls below 60% for 15 minutes
11. **High Network Traffic**: Triggers when network egress exceeds 5 MB/s for 5 minutes

## Interpreting Metrics

### Common Patterns to Watch For

#### Performance Degradation
- Increasing latency trends
- Correlation between high CPU/memory usage and latency

#### API Issues
- Spikes in error rates for specific endpoints
- Correlation between API errors and application errors

#### Resource Constraints
- Memory approaching limits
- Sustained high CPU usage

#### MCP Tool Performance
- High latency on specific MCP tools
- Error patterns in MCP tool usage

## Troubleshooting Common Issues

### High Latency
1. Check CPU and memory usage
2. Verify Google Ads API response times
3. Check for database contention if applicable
4. Examine logs for slow operations

### High Error Rates
1. Check application logs for exceptions
2. Verify Google Ads API credentials are valid
3. Check for rate limiting issues
4. Verify network connectivity

### Resource Constraints
1. Consider scaling up pod resources
2. Look for memory leaks
3. Optimize high-resource operations

### MCP Tool Issues
1. Check tool-specific logs for errors
2. Verify input validation is working correctly
3. Check for timeout configurations

## Extending the Monitoring

### Adding Custom Metrics

To add new metrics:

1. Update the `monitoring.py` file with additional metrics
2. Expose the metrics in the relevant application code
3. Add new panels to the dashboard using the JSON definition
4. Create additional alerting policies as needed

## Contact

For questions or issues with the monitoring setup, contact the DevOps team. 