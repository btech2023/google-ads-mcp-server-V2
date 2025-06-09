import asyncio
import cProfile
import logging
import pstats
import io
import time
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Callable, Union, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """
    Utility for profiling the performance of MCP tools and Google Ads service methods.
    
    This profiler measures execution time, memory usage, and API call counts
    for various operations to establish baseline performance metrics.
    """
    
    def __init__(self, output_dir: str = "performance_profiles"):
        """
        Initialize the performance profiler.
        
        Args:
            output_dir: Directory where profiling results will be saved
        """
        self.output_dir = output_dir
        self.baseline_metrics = {}
        self.results = {}
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    async def profile_async_function(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Profile an asynchronous function.
        
        Args:
            func: The async function to profile
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Dictionary with profiling results
        """
        # Prepare profiling
        pr = cProfile.Profile()
        start_time = time.time()
        
        # Start profiling
        pr.enable()
        
        # Execute function
        try:
            result = await func(*args, **kwargs)
            success = True
        except Exception as e:
            result = str(e)
            success = False
        
        # Stop profiling
        pr.disable()
        execution_time = time.time() - start_time
        
        # Process profiling statistics
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(30)  # Print top 30 functions by cumulative time
        
        # Extract memory usage (approximate)
        # This is primitive - for more accurate measurements, consider using memory_profiler
        memory_usage = 0  # Placeholder for actual measurement
        
        # Compile results
        profile_results = {
            "function_name": func.__name__,
            "execution_time": execution_time,
            "memory_usage": memory_usage,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "args": str(args),
            "kwargs": str(kwargs),
            "profile_stats": s.getvalue()
        }
        
        return profile_results
    
    async def profile_mcp_tool(self, tool_func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        Profile an MCP tool function.
        
        Args:
            tool_func: The MCP tool function to profile
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Dictionary with profiling results
        """
        logger.info(f"Profiling MCP tool: {tool_func.__name__}")
        return await self.profile_async_function(tool_func, *args, **kwargs)
    
    async def profile_service_method(self, service_instance: Any, method_name: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Profile a service method.
        
        Args:
            service_instance: Instance of the service class
            method_name: Name of the method to profile
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method
            
        Returns:
            Dictionary with profiling results
        """
        method = getattr(service_instance, method_name)
        logger.info(f"Profiling service method: {service_instance.__class__.__name__}.{method_name}")
        return await self.profile_async_function(method, *args, **kwargs)
    
    async def run_performance_suite(self, tests: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run a suite of performance tests.
        
        Args:
            tests: List of test configurations, each with:
                - 'name': Test name
                - 'type': 'mcp_tool', 'service_method', or 'function'
                - 'target': The function, (service_instance, method_name) tuple, or function object
                - 'args': Arguments to pass
                - 'kwargs': Keyword arguments to pass
                
        Returns:
            Dictionary mapping test names to their results
        """
        results = {}
        
        for test in tests:
            test_name = test['name']
            test_type = test['type']
            target = test['target']
            args = test.get('args', [])
            kwargs = test.get('kwargs', {})
            
            logger.info(f"Running performance test: {test_name}")
            
            try:
                if test_type == 'mcp_tool':
                    profile_result = await self.profile_mcp_tool(target, *args, **kwargs)
                elif test_type == 'service_method':
                    service_instance, method_name = target
                    profile_result = await self.profile_service_method(service_instance, method_name, *args, **kwargs)
                elif test_type == 'function':
                    # Target is the function itself
                    profile_result = await self.profile_async_function(target, *args, **kwargs)
                else:
                    logger.error(f"Unknown test type: {test_type}")
                    continue
                
                # Store results
                if test_name not in results:
                    results[test_name] = []
                
                results[test_name].append(profile_result)
                logger.info(f"Test {test_name} completed in {profile_result['execution_time']:.4f} seconds")
                
            except Exception as e:
                logger.error(f"Error running test {test_name}: {str(e)}")
        
        return results
    
    def save_results(self, results: Dict[str, List[Dict[str, Any]]], filename: str = None) -> str:
        """
        Save profiling results to a file.
        
        Args:
            results: The profiling results to save
            filename: Optional filename, defaults to a timestamp-based name
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"profile_results_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Serialize the results, handling non-serializable objects
        serializable_results = {}
        for test_name, test_results in results.items():
            serializable_results[test_name] = []
            for result in test_results:
                # Create a copy without profile_stats which can be very large
                serializable_result = {k: v for k, v in result.items() if k != 'profile_stats'}
                serializable_results[test_name].append(serializable_result)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        # Save detailed profile stats separately
        detailed_filepath = os.path.join(self.output_dir, f"detailed_{filename}.txt")
        with open(detailed_filepath, 'w') as f:
            for test_name, test_results in results.items():
                f.write(f"===== {test_name} =====\n\n")
                for i, result in enumerate(test_results):
                    f.write(f"--- Run {i+1} ---\n")
                    f.write(f"Execution time: {result['execution_time']:.4f} seconds\n")
                    f.write("Profile statistics:\n")
                    f.write(result.get('profile_stats', 'No profile stats available'))
                    f.write("\n\n")
        
        logger.info(f"Saved profiling results to {filepath}")
        logger.info(f"Saved detailed profile stats to {detailed_filepath}")
        
        return filepath
    
    def analyze_results(self, results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Analyze profiling results to extract insights.
        
        Args:
            results: The profiling results to analyze
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "summary": {},
            "details": {}
        }
        
        for test_name, test_results in results.items():
            # Calculate average execution time
            execution_times = [result['execution_time'] for result in test_results]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            max_execution_time = max(execution_times) if execution_times else 0
            min_execution_time = min(execution_times) if execution_times else 0
            
            # Calculate success rate
            success_count = sum(1 for result in test_results if result['success'])
            success_rate = success_count / len(test_results) if test_results else 0
            
            # Store summary
            analysis["summary"][test_name] = {
                "avg_execution_time": avg_execution_time,
                "max_execution_time": max_execution_time,
                "min_execution_time": min_execution_time,
                "success_rate": success_rate,
                "run_count": len(test_results)
            }
            
            # Store details
            analysis["details"][test_name] = {
                "execution_times": execution_times,
                "successes": [result['success'] for result in test_results]
            }
        
        return analysis


def log_performance_summary(summary: Dict[str, Any]) -> None:
    """Log a concise performance summary used by tests."""
    for name, metrics in summary.items():
        logger.info(
            "%s: avg %.4f sec over %d runs",
            name,
            metrics.get("avg_execution_time", 0),
            metrics.get("run_count", 0),
        )

# Example usage in a script:
"""
async def main():
    from google_ads.client import GoogleAdsService
    from google_ads.budgets import BudgetService
    from mcp.tools import get_budgets, get_budgets_json
    
    # Initialize services
    google_ads_service = GoogleAdsService()
    budget_service = BudgetService(google_ads_service)
    
    # Initialize profiler
    profiler = PerformanceProfiler()
    
    # Define tests
    tests = [
        {
            'name': 'get_budgets',
            'type': 'mcp_tool',
            'target': get_budgets,
            'args': ['1234567890']
        },
        {
            'name': 'get_budgets_json',
            'type': 'mcp_tool',
            'target': get_budgets_json,
            'args': ['1234567890']
        },
        {
            'name': 'budget_service_get_budgets',
            'type': 'service_method',
            'target': (budget_service, 'get_budgets'),
            'args': [],
            'kwargs': {'customer_id': '1234567890'}
        }
    ]
    
    # Run tests
    results = await profiler.run_performance_suite(tests)
    
    # Save results
    profiler.save_results(results)
    
    # Analyze results
    analysis = profiler.analyze_results(results)
    print(json.dumps(analysis['summary'], indent=2))

if __name__ == "__main__":
    asyncio.run(main())
""" 