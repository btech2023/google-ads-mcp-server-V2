#!/usr/bin/env python
"""
Test Batch Processing

This script tests the batch processing functionality by comparing
individual updates vs batch updates for multiple campaign budgets.
"""

import os
import sys
import asyncio
import logging
import time
import json
import random
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the shared mock client creator
from google_ads_mcp_server.tests.utils.mock_google_ads import create_mock_google_ads_client, DEFAULT_CUSTOMER_ID, MockBatchManager

# Use absolute imports
from google_ads_mcp_server.google_ads.batch_operations import BatchManager
from google_ads_mcp_server.utils.error_handler import ErrorDetails
from google_ads_mcp_server.utils.logging import configure_logging, get_logger
from google_ads.budgets import BudgetService

# Configure logging
configure_logging(console_level=logging.INFO)
logger = get_logger(__name__)

class BatchProcessingTest:
    """
    Tests batch processing functionality.
    """
    
    def __init__(self, customer_id: str):
        """
        Initialize the test suite.
        
        Args:
            customer_id: Google Ads customer ID for testing
        """
        self.customer_id = customer_id
        self.google_ads_client = None
        self.budget_service = None
        self.batch_manager = None
        
    async def setup(self):
        """Initialize necessary services using mocks."""
        self.google_ads_client = create_mock_google_ads_client()
        # Pass the mock client to the services
        self.budget_service = BudgetService(self.google_ads_client)
        # Use MockBatchManager instead of real BatchManager
        self.batch_manager = MockBatchManager()
        logger.info("Test setup completed")
        
    async def get_test_budgets(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get a list of test budgets to update.
        
        Args:
            limit: Maximum number of budgets to return
            
        Returns:
            List of budget data
        """
        budgets = await self.budget_service.get_budgets(
            customer_id=self.customer_id,
            status_filter="ENABLED"
        )
        
        # Return up to the limit
        test_budgets = budgets[:limit] if len(budgets) > limit else budgets
        logger.info(f"Retrieved {len(test_budgets)} test budgets")
        return test_budgets
        
    async def test_individual_updates(self, budgets: List[Dict[str, Any]]) -> float:
        """Test performance of individual budget updates."""
        logger.info(f"Testing individual updates for {len(budgets)} budgets")
        
        start_time = time.time() * 1000  # Convert to milliseconds
        success_count = 0
        
        for budget in budgets:
            budget_id = budget.get("id")
            # Test with a 10% increase in budget
            current_amount_micros = budget.get("amount_micros", 0)
            new_amount_micros = int(current_amount_micros * 1.1)
            
            result = await self.budget_service.update_budget(
                self.customer_id,
                budget_id,
                amount_micros=new_amount_micros
            )
            
            if result.get("success", False):
                success_count += 1
        
        end_time = time.time() * 1000
        elapsed_time = end_time - start_time
        
        success_rate = (success_count / len(budgets)) * 100 if budgets else 0
        logger.info(f"Individual updates completed in {elapsed_time:.2f}ms")
        logger.info(f"Individual updates success rate: {success_rate:.2f}% ({success_count}/{len(budgets)})")
        logger.info("")
        
        return elapsed_time
        
    async def test_batch_updates(self, budgets: List[Dict[str, Any]]) -> float:
        """Test performance of batch budget updates."""
        logger.info(f"Testing batch updates for {len(budgets)} budgets")
        
        # Create update operations for each budget
        update_operations = []
        for budget in budgets:
            budget_id = budget.get("id")
            # Test with a 10% increase in budget
            current_amount_micros = budget.get("amount_micros", 0)
            new_amount_micros = int(current_amount_micros * 1.1)
            
            update_operations.append({
                "budget_id": budget_id,
                "amount_micros": new_amount_micros
            })
        
        start_time = time.time() * 1000  # Convert to milliseconds
        results = await self.budget_service.update_budgets_batch(
            self.customer_id,
            update_operations
        )
        end_time = time.time() * 1000
        elapsed_time = end_time - start_time
        
        # Count successful operations
        success_count = 0
        if results:
            success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
        
        success_rate = (success_count / len(budgets)) * 100 if budgets else 0
        logger.info(f"Batch updates completed in {elapsed_time:.2f}ms")
        logger.info(f"Batch updates success rate: {success_rate:.2f}% ({success_count}/{len(budgets)})")
        
        return elapsed_time
        
    async def test_direct_batch_manager(self, budgets: List[Dict[str, Any]]) -> float:
        """Test performance using the BatchManager directly."""
        logger.info(f"Testing direct batch manager for {len(budgets)} budgets")
        
        # Reset batch to start fresh
        self.batch_manager.reset_batch()
        
        # Add budget update operations to batch
        for budget in budgets:
            budget_id = budget.get("id")
            current_amount_micros = budget.get("amount_micros", 0)
            new_amount_micros = int(current_amount_micros * 1.1)
            
            self.batch_manager.add_budget_update({
                "customer_id": self.customer_id,
                "budget_id": budget_id,
                "amount_micros": new_amount_micros
            })
        
        start_time = time.time() * 1000
        results = await self.batch_manager.execute_batch()
        end_time = time.time() * 1000
        elapsed_time = end_time - start_time
        
        # Count successful operations
        success_count = sum(1 for r in results if r.get("status") == "SUCCESS")
        success_rate = (success_count / len(budgets)) * 100 if budgets else 0
        
        logger.info(f"Direct batch manager completed in {elapsed_time:.2f}ms")
        logger.info(f"Direct batch success rate: {success_rate:.2f}% ({success_count}/{len(budgets)})")
        
        return elapsed_time
    
    async def run_tests(self):
        """Run all batch processing tests"""
        await self.setup()
        
        logger.info("=" * 60)
        logger.info("STARTING BATCH PROCESSING TESTS")
        logger.info("=" * 60)
        
        # Get test budgets
        test_budgets = await self.get_test_budgets(limit=5)
        
        if not test_budgets:
            logger.error("No test budgets found. Tests cannot proceed.")
            return
            
        # Run tests
        individual_time = await self.test_individual_updates(test_budgets)
        batch_time = await self.test_batch_updates(test_budgets)
        direct_time = await self.test_direct_batch_manager(test_budgets)
        
        # Compare performance
        if individual_time > 0 and batch_time > 0:
            improvement = (individual_time - batch_time) / individual_time * 100
            logger.info(f"Performance improvement: {improvement:.2f}% faster with batch processing")
            logger.info(f"Individual vs Batch: {individual_time:.2f}ms vs {batch_time:.2f}ms")
            logger.info(f"Direct batch manager: {direct_time:.2f}ms")
        
        # Calculate improvement
        individual_per_op = individual_time / len(test_budgets)
        batch_per_op = batch_time / len(test_budgets)
        direct_per_op = direct_time / len(test_budgets)
        
        batch_improvement = ((individual_time - batch_time) / individual_time) * 100
        direct_improvement = ((individual_time - direct_time) / individual_time) * 100
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("BATCH PROCESSING TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Number of budgets tested: {len(test_budgets)}")
        logger.info(f"Individual updates: {individual_time:.2f}ms total, {individual_per_op:.2f}ms per operation")
        logger.info(f"Batch updates (service): {batch_time:.2f}ms total, {batch_per_op:.2f}ms per operation")
        logger.info(f"Batch updates (direct): {direct_time:.2f}ms total, {direct_per_op:.2f}ms per operation")
        logger.info(f"Improvement (service): {batch_improvement:.2f}%")
        logger.info(f"Improvement (direct): {direct_improvement:.2f}%")
        
        # Provide recommendation
        if batch_improvement > 10 or direct_improvement > 10:
            logger.info("\nRECOMMENDATION: Batch processing provides significant performance benefits and should be used for bulk operations.")
        else:
            logger.info("\nRECOMMENDATION: Performance benefits of batch processing are minimal in this case, but it may still reduce API quota usage.")
        
        logger.info("Tests completed successfully!")
        
async def main():
    """Main function to run tests"""
    if len(sys.argv) < 2:
        print("Usage: python test_batch_processing.py <customer_id>")
        print("Example: python test_batch_processing.py 1234567890")
        sys.exit(1)
        
    customer_id = sys.argv[1]
    test = BatchProcessingTest(customer_id)
    await test.run_tests()

if __name__ == "__main__":
    asyncio.run(main()) 