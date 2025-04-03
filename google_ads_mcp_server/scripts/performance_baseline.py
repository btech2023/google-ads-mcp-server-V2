#!/usr/bin/env python
"""
Performance Baseline Test Script

This script establishes performance baselines for key MCP tools and Google Ads service methods
as part of Project NOVA ULTRA Phase 2: Performance Optimization.

It measures:
- Execution time
- Memory usage (where possible)
- API call patterns
- Success rates

Results are saved to JSON files in the performance_profiles directory.
"""

import asyncio
import os
import json
import sys
import logging
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.performance_profiler import PerformanceProfiler
from google_ads.client import GoogleAdsService
from google_ads.budgets import BudgetService
from google_ads.ad_groups import AdGroupService
from google_ads.keywords import KeywordService
from google_ads.search_terms import SearchTermService
from google_ads.dashboards import DashboardService
from google_ads.insights import InsightsService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
DEFAULT_CUSTOMER_ID = "1234567890"  # Replace with a valid test customer ID
DEFAULT_START_DATE = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")
DEFAULT_RUNS_PER_TEST = 3  # Number of times to run each test for averaging

async def main():
    """Main entry point for the performance baseline script."""
    logger.info("Starting performance baseline tests...")
    
    # Get customer ID from argument or use default
    customer_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CUSTOMER_ID
    runs_per_test = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_RUNS_PER_TEST
    
    logger.info(f"Using customer ID: {customer_id}")
    logger.info(f"Running each test {runs_per_test} times")
    
    # Initialize profiler
    profile_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "performance_profiles")
    profiler = PerformanceProfiler(output_dir=profile_dir)
    
    # Initialize services
    google_ads_service = GoogleAdsService()
    budget_service = BudgetService(google_ads_service)
    ad_group_service = AdGroupService(google_ads_service)
    keyword_service = KeywordService(google_ads_service)
    search_term_service = SearchTermService(google_ads_service)
    dashboard_service = DashboardService(google_ads_service)
    insights_service = InsightsService(google_ads_service)
    
    # Define test batches
    test_batches = {
        "budget_tests": get_budget_tests(customer_id, budget_service),
        "ad_group_tests": get_ad_group_tests(customer_id, ad_group_service),
        "keyword_tests": get_keyword_tests(customer_id, keyword_service),
        "search_term_tests": get_search_term_tests(customer_id, search_term_service),
        "dashboard_tests": get_dashboard_tests(customer_id, dashboard_service),
        "insights_tests": get_insights_tests(customer_id, insights_service),
        "complex_visualization_tests": get_complex_visualization_tests(
            customer_id, budget_service, dashboard_service, insights_service
        )
    }
    
    # Run tests batch by batch
    all_results = {}
    
    for batch_name, tests in test_batches.items():
        logger.info(f"Running test batch: {batch_name}")
        
        # Run each test multiple times
        for test in tests:
            for _ in range(runs_per_test - 1):  # -1 because the run_performance_suite will run it once
                test_copy = test.copy()
                if 'name' in test_copy:
                    # Modify the name to avoid overwriting results
                    test_copy['name'] = f"{test_copy['name']}_run_{_+1}"
                tests.append(test_copy)
        
        # Run the tests
        results = await profiler.run_performance_suite(tests)
        
        # Save results for this batch
        batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profiler.save_results(results, f"{batch_name}_{batch_timestamp}.json")
        
        # Analyze results
        analysis = profiler.analyze_results(results)
        logger.info(f"{batch_name} summary:")
        for test_name, summary in analysis['summary'].items():
            logger.info(f"  {test_name}: {summary['avg_execution_time']:.4f}s avg, {summary['success_rate']*100:.1f}% success")
        
        # Merge with all results
        all_results.update(results)
    
    # Save combined results
    combined_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    profiler.save_results(all_results, f"all_tests_{combined_timestamp}.json")
    
    # Generate final summary
    final_analysis = profiler.analyze_results(all_results)
    summary_path = os.path.join(profile_dir, f"summary_{combined_timestamp}.json")
    with open(summary_path, 'w') as f:
        json.dump(final_analysis['summary'], f, indent=2)
    
    logger.info(f"Performance baseline testing complete. Summary saved to {summary_path}")

def get_budget_tests(customer_id, budget_service):
    """Get budget-related performance tests."""
    return [
        {
            'name': 'budget_service_get_budgets',
            'type': 'service_method',
            'target': (budget_service, 'get_budgets'),
            'kwargs': {'customer_id': customer_id}
        },
        {
            'name': 'budget_service_analyze_budget_performance',
            'type': 'service_method',
            'target': (budget_service, 'analyze_budget_performance'),
            'kwargs': {'customer_id': customer_id}
        }
    ]

def get_ad_group_tests(customer_id, ad_group_service):
    """Get ad group-related performance tests."""
    return [
        {
            'name': 'ad_group_service_get_ad_groups',
            'type': 'service_method',
            'target': (ad_group_service, 'get_ad_groups'),
            'kwargs': {'customer_id': customer_id}
        },
        {
            'name': 'ad_group_service_get_ad_group_performance',
            'type': 'service_method',
            'target': (ad_group_service, 'get_ad_group_performance'),
            'kwargs': {
                'customer_id': customer_id,
                'ad_group_id': '123456789',  # Replace with a valid ad group ID
                'start_date': DEFAULT_START_DATE,
                'end_date': DEFAULT_END_DATE
            }
        }
    ]

def get_keyword_tests(customer_id, keyword_service):
    """Get keyword-related performance tests."""
    return [
        {
            'name': 'keyword_service_get_keywords',
            'type': 'service_method',
            'target': (keyword_service, 'get_keywords'),
            'kwargs': {
                'customer_id': customer_id,
                'start_date': DEFAULT_START_DATE,
                'end_date': DEFAULT_END_DATE
            }
        }
    ]

def get_search_term_tests(customer_id, search_term_service):
    """Get search term-related performance tests."""
    return [
        {
            'name': 'search_term_service_get_search_terms_report',
            'type': 'service_method',
            'target': (search_term_service, 'get_search_terms_report'),
            'kwargs': {
                'customer_id': customer_id,
                'start_date': DEFAULT_START_DATE,
                'end_date': DEFAULT_END_DATE
            }
        },
        {
            'name': 'search_term_service_analyze_search_terms',
            'type': 'service_method',
            'target': (search_term_service, 'analyze_search_terms'),
            'kwargs': {
                'customer_id': customer_id,
                'start_date': DEFAULT_START_DATE,
                'end_date': DEFAULT_END_DATE
            }
        }
    ]

def get_dashboard_tests(customer_id, dashboard_service):
    """Get dashboard-related performance tests."""
    return [
        {
            'name': 'dashboard_service_get_account_dashboard',
            'type': 'service_method',
            'target': (dashboard_service, 'get_account_dashboard'),
            'kwargs': {
                'customer_id': customer_id,
                'start_date': DEFAULT_START_DATE,
                'end_date': DEFAULT_END_DATE
            }
        },
        {
            'name': 'dashboard_service_get_campaign_dashboard',
            'type': 'service_method',
            'target': (dashboard_service, 'get_campaign_dashboard'),
            'kwargs': {
                'customer_id': customer_id,
                'campaign_id': '1234567890',  # Replace with a valid campaign ID
                'start_date': DEFAULT_START_DATE,
                'end_date': DEFAULT_END_DATE
            }
        }
    ]

def get_insights_tests(customer_id, insights_service):
    """Get insights-related performance tests."""
    return [
        {
            'name': 'insights_service_detect_performance_anomalies',
            'type': 'service_method',
            'target': (insights_service, 'detect_performance_anomalies'),
            'kwargs': {
                'customer_id': customer_id,
                'start_date': DEFAULT_START_DATE,
                'end_date': DEFAULT_END_DATE
            }
        },
        {
            'name': 'insights_service_generate_optimization_suggestions',
            'type': 'service_method',
            'target': (insights_service, 'generate_optimization_suggestions'),
            'kwargs': {
                'customer_id': customer_id
            }
        },
        {
            'name': 'insights_service_discover_opportunities',
            'type': 'service_method',
            'target': (insights_service, 'discover_opportunities'),
            'kwargs': {
                'customer_id': customer_id
            }
        }
    ]

def get_complex_visualization_tests(customer_id, budget_service, dashboard_service, insights_service):
    """Get tests for complex visualization operations that may be performance-intensive."""
    return [
        {
            'name': 'complex_dashboard_with_visualization',
            'type': 'service_method',
            'target': (dashboard_service, 'get_account_dashboard'),
            'kwargs': {
                'customer_id': customer_id,
                'start_date': DEFAULT_START_DATE,
                'end_date': DEFAULT_END_DATE,
                'include_visualization': True
            }
        },
        {
            'name': 'complex_insights_with_visualization',
            'type': 'service_method',
            'target': (insights_service, 'detect_performance_anomalies'),
            'kwargs': {
                'customer_id': customer_id,
                'start_date': DEFAULT_START_DATE,
                'end_date': DEFAULT_END_DATE,
                'include_visualization': True
            }
        },
        {
            'name': 'budget_analysis_with_visualization',
            'type': 'service_method',
            'target': (budget_service, 'analyze_budget_performance'),
            'kwargs': {
                'customer_id': customer_id,
                'include_visualization': True
            }
        }
    ]

if __name__ == "__main__":
    asyncio.run(main()) 