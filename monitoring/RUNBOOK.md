# Google Ads MCP Server Monitoring Runbook

This runbook provides guidance for responding to alerts and troubleshooting issues with the Google Ads MCP Server.

## Alert Response Guide

### High API Latency Alert

**Alert Description:** P95 latency exceeds 1 second for 5 minutes or more.

**Possible Causes:**
- High server load
- Network congestion
- Google Ads API throttling or slowdown
- Resource contention in the cluster

**Response Steps:**
1. Check CPU and memory usage in the monitoring dashboard
2. Verify Google Ads API status at https://ads.google.com/status/
3. Look for concurrent high-traffic operations
4. Check pod logs for any errors or timeouts:
   ```
   kubectl logs -n dev -l app=google-ads-mcp-server
   ```
5. Consider scaling up the deployment if needed:
   ```
   kubectl scale deployment google-ads-mcp-server -n dev --replicas=3
   ```

### High HTTP Error Rate Alert

**Alert Description:** Error rate exceeds 5% for 5 minutes or more.

**Possible Causes:**
- Application code errors
- Invalid client requests
- API authentication issues
- Resource limitations

**Response Steps:**
1. Check the logs for specific error messages:
   ```
   kubectl logs -n dev -l app=google-ads-mcp-server | grep -i error
   ```
2. Verify if errors are client-side or server-side by analyzing response codes
3. Check for patterns in the error timing or specific endpoints
4. Verify Google Ads API credentials are valid
5. If necessary, perform a rolling restart:
   ```
   kubectl rollout restart deployment google-ads-mcp-server -n dev
   ```

### Google Ads API Errors Alert

**Alert Description:** Google Ads API error rate exceeds 2% for 5 minutes.

**Possible Causes:**
- Invalid API credentials
- Rate limiting
- API changes
- Account issues

**Response Steps:**
1. Check Google Ads API logs for specific error codes
2. Verify credentials configuration:
   ```
   kubectl describe secret google-ads-credentials -n dev
   ```
3. Check Google Ads API status page
4. If rate-limited, implement exponential backoff
5. For authentication errors, refresh the OAuth tokens

### High Memory/CPU Usage Alert

**Alert Description:** Memory/CPU usage exceeds 80% of limit for 5 minutes.

**Possible Causes:**
- Traffic spike
- Memory leak
- Inefficient code
- Background processes consuming resources

**Response Steps:**
1. Check if usage is due to normal traffic increase
2. Look for memory leaks by monitoring growth over time
3. Consider vertical scaling by increasing resource limits:
   ```
   kubectl edit deployment google-ads-mcp-server -n dev
   ```
4. Enable profiling to identify bottlenecks
5. Implement horizontal scaling if needed

### Health Check Failure Alert

**Alert Description:** Application health check reports DOWN status.

**Possible Causes:**
- Application crashed
- Database connection issues
- Dependency failure
- Networking problems

**Response Steps:**
1. Check pod status:
   ```
   kubectl get pods -n dev -l app=google-ads-mcp-server
   ```
2. Check pod logs for errors during startup
3. Verify all dependencies are accessible
4. Attempt a restart:
   ```
   kubectl rollout restart deployment google-ads-mcp-server -n dev
   ```
5. Check deployment configuration for errors

### Pod Restarts Alert

**Alert Description:** Pods have restarted in the last 10 minutes.

**Possible Causes:**
- Out of memory (OOMKilled)
- Application crashes
- Readiness/liveness probe failures
- Node issues

**Response Steps:**
1. Check the pod's previous logs:
   ```
   kubectl logs -n dev -l app=google-ads-mcp-server --previous
   ```
2. Check events in the namespace:
   ```
   kubectl get events -n dev
   ```
3. Look for OOMKilled status, which indicates memory issues
4. If memory issues, increase the memory limits
5. If application crashes, check for code issues in recent deployments

### MCP Tool Errors Alert

**Alert Description:** MCP tool error rate exceeds 3% for 5 minutes.

**Possible Causes:**
- Incompatible client requests
- Tool implementation issues
- Google Ads API data issues
- Validation failures

**Response Steps:**
1. Check logs for specific MCP tool errors
2. Analyze client request patterns
3. Verify Google Ads API responses are as expected
4. If a specific tool is problematic, consider restricting its use temporarily

### Low Cache Hit Rate Alert

**Alert Description:** Cache hit rate falls below 60% for 15 minutes.

**Possible Causes:**
- Cache invalidation
- New query patterns
- Cache configuration issues
- Cold start after deployment

**Response Steps:**
1. Check if there was a recent deployment (cold cache)
2. Analyze query patterns for changes
3. Verify cache configuration is correct
4. Consider adjusting cache TTL or size
5. Monitor performance impact and adjust cache strategy

## Metrics Interpretation Guide

### HTTP Performance Metrics

- **Request Count by Status**: Shows total HTTP requests segmented by status code.
  - High 4xx errors indicate client issues
  - High 5xx errors indicate server issues
  - Sudden drops in 2xx may indicate availability problems

- **Latency (p95)**: Shows the 95th percentile of request latency.
  - Steady increase may indicate growing performance issues
  - Spikes may indicate temporary bottlenecks
  - Correlate with CPU/Memory for resource constraints

### Google Ads API Metrics

- **API Requests**: Shows API call volume by endpoint and status.
  - High error rates on specific endpoints may indicate issues with those API features
  - Overall volume helps understand API usage patterns

- **API Latency**: Shows response time for Google Ads API calls.
  - Helps identify slow API operations
  - Can be used to optimize high-latency operations

### Cache Performance Metrics

- **Cache Hits/Misses**: Shows cache efficiency.
  - Low hit rate may indicate ineffective caching strategy
  - High miss rate with high traffic may increase API costs

### System Resource Metrics

- **Memory Usage**: Shows memory consumption versus limits.
  - Steady increase may indicate memory leaks
  - Regular patterns may indicate memory-intensive operations

- **CPU Usage**: Shows processing power consumption.
  - Correlates with request volume and complexity
  - Sustained high usage may require scaling

- **Network Traffic**: Shows ingress/egress data volume.
  - Abnormal spikes may indicate unusual data transfer or attacks
  - Helps size network resources appropriately

## Common Troubleshooting Procedures

### Investigating Pod Crashes

1. Get pod details:
   ```
   kubectl describe pod -n dev <pod-name>
   ```

2. Check previous logs:
   ```
   kubectl logs -n dev <pod-name> --previous
   ```

3. Check events:
   ```
   kubectl get events -n dev --sort-by=.metadata.creationTimestamp
   ```

4. Check container status and reason for termination:
   ```
   kubectl get pod -n dev <pod-name> -o json | jq '.status.containerStatuses'
   ```

### Debugging API Failures

1. Enable debug logging by setting environment variable:
   ```
   kubectl set env deployment/google-ads-mcp-server -n dev LOG_LEVEL=DEBUG
   ```

2. Verify API credentials:
   ```
   kubectl describe secret google-ads-credentials -n dev
   ```

3. Check for rate limiting headers in logs

4. Verify network connectivity to Google APIs:
   ```
   kubectl exec -it -n dev <pod-name> -- curl -v https://googleads.googleapis.com/
   ```

### Performance Optimization

1. Review resource usage patterns over time in the dashboard

2. Identify top API consumers from logs:
   ```
   kubectl logs -n dev -l app=google-ads-mcp-server | grep "API request" | sort | uniq -c | sort -nr | head -10
   ```

3. Check for slow database queries (if applicable)

4. Consider implementing targeted caching for frequently used data

5. Review code for optimization opportunities in high-traffic areas

## Monthly Monitoring Review Checklist

- [ ] Review alert history for patterns
- [ ] Adjust thresholds for any alerts with high false positive rates
- [ ] Verify notification channels are working correctly
- [ ] Update runbook with new troubleshooting procedures
- [ ] Check resource utilization trends for capacity planning
- [ ] Review dashboard effectiveness and adjust if needed

## Escalation Procedures

### Level 1: On-Call Engineer
- Responds to initial alerts
- Follows runbook procedures
- Resolves common issues
- Escalates if issue persists for >30 minutes

### Level 2: Technical Lead
- Handles complex issues
- Reviews system architecture implications
- Makes decisions on service degradation
- Escalates for business impact decisions

### Level 3: Engineering Manager
- Coordinates cross-team responses
- Communicates with stakeholders
- Makes resource allocation decisions
- Approves emergency changes

## Notification Recipients

| Alert Priority | Recipients | Contact Method |
|---------------|------------|---------------|
| Critical | On-Call Engineer + Technical Lead | Email + SMS |
| Warning | On-Call Engineer | Email |
| Info | Monitoring Email Group | Email |

**Current Primary Contact:** Bjorn Hansen (bjorndavidhansen@gmail.com)

---

## References

- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [Kubernetes Debugging](https://kubernetes.io/docs/tasks/debug/)
- [GCP Monitoring Documentation](https://cloud.google.com/monitoring/docs)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/) 