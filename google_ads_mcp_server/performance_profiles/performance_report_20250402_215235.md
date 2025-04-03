# Google Ads MCP Server - Performance Analysis Report

Generated: 2025-04-02 21:52:35

**Note: This is a simulated report for project planning purposes.**

## Performance Summary

| Test | Avg Time (s) | Min Time (s) | Max Time (s) | Success Rate |
|------|-------------|-------------|-------------|-------------|
| insights_service_generate_optimization_suggestions | 5.3001 | 5.2040 | 5.4010 | 100.0% |
| complex_insights_with_visualization | 5.1303 | 3.0618 | 7.0935 | 66.7% |
| insights_service_discover_opportunities | 5.0568 | 3.4993 | 5.8644 | 100.0% |
| get_performance_anomalies_json | 4.5506 | 2.6999 | 6.9093 | 100.0% |
| dashboard_service_get_account_dashboard | 4.2351 | 3.8949 | 4.7209 | 100.0% |
| insights_service_detect_performance_anomalies | 4.1347 | 3.9150 | 4.5573 | 100.0% |
| complex_dashboard_with_visualization | 4.0048 | 2.8936 | 5.4037 | 66.7% |
| budget_analysis_with_visualization | 3.2368 | 2.4896 | 3.8530 | 100.0% |
| create_breakdown_visualization | 3.2273 | 2.3688 | 3.7132 | 33.3% |
| search_term_service_get_search_terms_report | 3.0363 | 2.5654 | 3.8706 | 100.0% |
| get_account_dashboard_json | 2.9258 | 1.7595 | 4.2568 | 100.0% |
| create_comparison_bar_chart | 2.5973 | 2.1688 | 3.2759 | 100.0% |
| search_term_service_analyze_search_terms | 2.5717 | 2.0495 | 3.3320 | 100.0% |
| budget_service_analyze_budget_performance | 2.4062 | 0.8881 | 3.2495 | 100.0% |
| analyze_budgets | 2.3946 | 1.4878 | 3.4939 | 100.0% |
| dashboard_service_get_campaign_dashboard | 2.3347 | 1.5659 | 3.7166 | 100.0% |
| ad_group_service_get_ad_group_performance | 2.0337 | 1.3986 | 2.3778 | 100.0% |
| get_ad_groups_json | 1.7838 | 1.5412 | 2.1372 | 100.0% |
| keyword_service_get_keywords | 1.7170 | 1.2037 | 2.5326 | 66.7% |
| get_budgets_json | 1.5511 | 0.9958 | 2.4931 | 100.0% |
| budget_service_get_budgets | 1.4210 | 1.0280 | 1.7493 | 100.0% |
| get_keywords_json | 1.3511 | 1.0328 | 1.5123 | 100.0% |
| ad_group_service_get_ad_groups | 0.8178 | 0.5950 | 1.2361 | 100.0% |

## Optimization Targets

The following tests are identified as potential optimization targets based on execution time:

1. **insights_service_generate_optimization_suggestions** - 5.3001 seconds
2. **complex_insights_with_visualization** - 5.1303 seconds
3. **insights_service_discover_opportunities** - 5.0568 seconds
4. **get_performance_anomalies_json** - 4.5506 seconds
5. **dashboard_service_get_account_dashboard** - 4.2351 seconds

## Performance Classification

Tests are classified into the following categories:

- **Critical** (> 5 seconds): Severe performance bottlenecks requiring immediate attention
- **Slow** (2-5 seconds): Performance issues that should be addressed
- **Moderate** (1-2 seconds): Worth optimizing if time permits
- **Fast** (< 1 second): Acceptable performance

### Critical Paths

- insights_service_generate_optimization_suggestions (5.3001 seconds)
- complex_insights_with_visualization (5.1303 seconds)
- insights_service_discover_opportunities (5.0568 seconds)

### Slow Paths

- get_performance_anomalies_json (4.5506 seconds)
- dashboard_service_get_account_dashboard (4.2351 seconds)
- insights_service_detect_performance_anomalies (4.1347 seconds)
- complex_dashboard_with_visualization (4.0048 seconds)
- budget_analysis_with_visualization (3.2368 seconds)
- create_breakdown_visualization (3.2273 seconds)
- search_term_service_get_search_terms_report (3.0363 seconds)
- get_account_dashboard_json (2.9258 seconds)
- create_comparison_bar_chart (2.5973 seconds)
- search_term_service_analyze_search_terms (2.5717 seconds)
- budget_service_analyze_budget_performance (2.4062 seconds)
- analyze_budgets (2.3946 seconds)
- dashboard_service_get_campaign_dashboard (2.3347 seconds)
- ad_group_service_get_ad_group_performance (2.0337 seconds)

### Moderate Paths

- get_ad_groups_json (1.7838 seconds)
- keyword_service_get_keywords (1.7170 seconds)
- get_budgets_json (1.5511 seconds)
- budget_service_get_budgets (1.4210 seconds)
- get_keywords_json (1.3511 seconds)

### Fast Paths

- ad_group_service_get_ad_groups (0.8178 seconds)
