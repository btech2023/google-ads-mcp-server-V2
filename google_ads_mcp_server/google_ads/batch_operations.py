"""
Batch Operations Module

This module provides batch processing capabilities for Google Ads API operations,
allowing multiple operations to be grouped together and executed in a single API call
for improved performance and reduced API quota usage.
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional, Union, Tuple, Callable
from enum import Enum
from google.ads.googleads.errors import GoogleAdsException

from .client_base import GoogleAdsClientError

logger = logging.getLogger(__name__)

class OperationType(Enum):
    """Types of operations supported in batch processing."""
    CAMPAIGN_BUDGET = "campaign_budget"
    CAMPAIGN = "campaign"
    AD_GROUP = "ad_group"
    AD_GROUP_AD = "ad_group_ad"
    AD_GROUP_CRITERION = "ad_group_criterion"
    KEYWORD = "keyword"


class BatchOperation:
    """Represents a single operation in a batch."""
    
    def __init__(self, 
                 operation_type: OperationType, 
                 operation_id: str,
                 operation_data: Dict[str, Any],
                 customer_id: str):
        """
        Initialize a batch operation.
        
        Args:
            operation_type: Type of operation (budget, campaign, etc.)
            operation_id: Unique identifier for the operation
            operation_data: Data for the operation
            customer_id: Customer ID for the operation
        """
        self.operation_type = operation_type
        self.operation_id = operation_id
        self.operation_data = operation_data
        self.customer_id = customer_id
        self.status = "PENDING"
        self.result = None
        self.error = None


class BatchManager:
    """
    Manages batched Google Ads API operations.
    """
    
    def __init__(self, google_ads_service):
        """
        Initialize the BatchManager.
        
        Args:
            google_ads_service: An initialized GoogleAdsService instance
        """
        self.google_ads_service = google_ads_service
        self.operations = []
        self.max_batch_size = 1000  # Google's recommendation
        self.client = google_ads_service.client
        self.logger = logging.getLogger(__name__)
        self.logger.info("BatchManager initialized")

    def add_operation(self, 
                      operation_type: OperationType, 
                      operation_id: str,
                      operation_data: Dict[str, Any],
                      customer_id: str) -> str:
        """
        Add an operation to the batch.
        
        Args:
            operation_type: Type of operation (budget, campaign, etc.)
            operation_id: Unique identifier for the operation
            operation_data: Data for the operation
            customer_id: Customer ID for the operation
            
        Returns:
            ID of the added operation
        """
        operation = BatchOperation(operation_type, operation_id, operation_data, customer_id)
        self.operations.append(operation)
        self.logger.info(f"Added {operation_type.value} operation with ID {operation_id} to batch")
        return operation_id
    
    def add_campaign_budget_update(self, 
                                  budget_id: str, 
                                  amount_micros: int, 
                                  customer_id: str) -> str:
        """
        Add a campaign budget update operation to the batch.
        
        Args:
            budget_id: ID of the budget to update
            amount_micros: New budget amount in micros
            customer_id: Customer ID for the operation
            
        Returns:
            ID of the added operation
        """
        operation_data = {
            "budget_id": budget_id,
            "amount_micros": amount_micros,
        }
        return self.add_operation(
            operation_type=OperationType.CAMPAIGN_BUDGET,
            operation_id=f"budget_update_{budget_id}",
            operation_data=operation_data,
            customer_id=customer_id
        )
    
    def add_ad_group_update(self, 
                          ad_group_id: str, 
                          updates: Dict[str, Any], 
                          customer_id: str) -> str:
        """
        Add an ad group update operation to the batch.
        
        Args:
            ad_group_id: ID of the ad group to update
            updates: Dictionary of fields to update
            customer_id: Customer ID for the operation
            
        Returns:
            ID of the added operation
        """
        operation_data = {
            "ad_group_id": ad_group_id,
            "updates": updates
        }
        return self.add_operation(
            operation_type=OperationType.AD_GROUP,
            operation_id=f"ad_group_update_{ad_group_id}",
            operation_data=operation_data,
            customer_id=customer_id
        )
    
    def add_keyword_update(self, 
                         keyword_id: str, 
                         updates: Dict[str, Any], 
                         customer_id: str) -> str:
        """
        Add a keyword update operation to the batch.
        
        Args:
            keyword_id: ID of the keyword to update
            updates: Dictionary of fields to update
            customer_id: Customer ID for the operation
            
        Returns:
            ID of the added operation
        """
        operation_data = {
            "keyword_id": keyword_id,
            "updates": updates
        }
        return self.add_operation(
            operation_type=OperationType.KEYWORD,
            operation_id=f"keyword_update_{keyword_id}",
            operation_data=operation_data,
            customer_id=customer_id
        )
    
    def _create_budget_operation(self, operation: BatchOperation) -> Dict[str, Any]:
        """
        Create a campaign budget operation.
        
        Args:
            operation: The batch operation
            
        Returns:
            Google Ads API operation object
        """
        data = operation.operation_data
        budget_id = data["budget_id"]
        amount_micros = data["amount_micros"]
        customer_id = operation.customer_id
        
        # Get services
        campaign_budget_service = self.client.get_service("CampaignBudgetService")
        
        # Create the budget resource name
        resource_name = campaign_budget_service.campaign_budget_path(customer_id, budget_id)
        
        # Create and configure the budget update operation
        campaign_budget_operation = self.client.get_type("CampaignBudgetOperation")
        campaign_budget = campaign_budget_operation.update
        campaign_budget.resource_name = resource_name
        campaign_budget.amount_micros = amount_micros
        
        # Create field mask for amount_micros field
        field_mask = self.client.get_type("FieldMask")
        field_mask.paths.append("amount_micros")
        campaign_budget_operation.update_mask = field_mask
        
        return {
            "operation": campaign_budget_operation,
            "service": campaign_budget_service,
            "method": "mutate_campaign_budgets"
        }
    
    def _create_ad_group_operation(self, operation: BatchOperation) -> Dict[str, Any]:
        """
        Create an ad group operation.
        
        Args:
            operation: The batch operation
            
        Returns:
            Google Ads API operation object
        """
        data = operation.operation_data
        ad_group_id = data["ad_group_id"]
        updates = data["updates"]
        customer_id = operation.customer_id
        
        # Get services
        ad_group_service = self.client.get_service("AdGroupService")
        
        # Create the ad group resource name
        resource_name = ad_group_service.ad_group_path(customer_id, ad_group_id)
        
        # Create and configure the ad group update operation
        ad_group_operation = self.client.get_type("AdGroupOperation")
        ad_group = ad_group_operation.update
        ad_group.resource_name = resource_name
        
        # Add update fields
        field_mask = self.client.get_type("FieldMask")
        for field, value in updates.items():
            if field == "name":
                ad_group.name = value
                field_mask.paths.append("name")
            elif field == "status":
                ad_group.status = self.client.enums.AdGroupStatusEnum[value]
                field_mask.paths.append("status")
            elif field == "cpc_bid_micros":
                ad_group.cpc_bid_micros = value
                field_mask.paths.append("cpc_bid_micros")
        
        ad_group_operation.update_mask = field_mask
        
        return {
            "operation": ad_group_operation,
            "service": ad_group_service,
            "method": "mutate_ad_groups"
        }
    
    def _create_keyword_operation(self, operation: BatchOperation) -> Dict[str, Any]:
        """
        Create a keyword operation.
        
        Args:
            operation: The batch operation
            
        Returns:
            Google Ads API operation object
        """
        data = operation.operation_data
        keyword_id = data["keyword_id"]
        updates = data["updates"]
        customer_id = operation.customer_id
        
        # Get services
        ad_group_criterion_service = self.client.get_service("AdGroupCriterionService")
        
        # Create the ad group criterion resource name
        ad_group_id = None
        if "ad_group_id" in updates:
            ad_group_id = updates["ad_group_id"]
            
        resource_name = ad_group_criterion_service.ad_group_criterion_path(
            customer_id, ad_group_id, keyword_id) if ad_group_id else f"customers/{customer_id}/adGroupCriteria/{keyword_id}"
        
        # Create and configure the criterion update operation
        criterion_operation = self.client.get_type("AdGroupCriterionOperation")
        criterion = criterion_operation.update
        criterion.resource_name = resource_name
        
        # Add update fields
        field_mask = self.client.get_type("FieldMask")
        for field, value in updates.items():
            if field == "status":
                criterion.status = self.client.enums.AdGroupCriterionStatusEnum[value]
                field_mask.paths.append("status")
            elif field == "cpc_bid_micros":
                criterion.cpc_bid_micros = value
                field_mask.paths.append("cpc_bid_micros")
        
        criterion_operation.update_mask = field_mask
        
        return {
            "operation": criterion_operation,
            "service": ad_group_criterion_service,
            "method": "mutate_ad_group_criteria"
        }
    
    def _create_operation(self, operation: BatchOperation) -> Optional[Dict[str, Any]]:
        """
        Create a Google Ads API operation based on the operation type.
        
        Args:
            operation: The batch operation
            
        Returns:
            Google Ads API operation object, or None if the operation type is not supported
        """
        if operation.operation_type == OperationType.CAMPAIGN_BUDGET:
            return self._create_budget_operation(operation)
        elif operation.operation_type == OperationType.AD_GROUP:
            return self._create_ad_group_operation(operation)
        elif operation.operation_type == OperationType.KEYWORD:
            return self._create_keyword_operation(operation)
        else:
            self.logger.warning(f"Unsupported operation type: {operation.operation_type.value}")
            return None
    
    async def execute_batch(self) -> List[Dict[str, Any]]:
        """
        Execute all operations in the batch.
        
        Returns:
            List of results for each operation
        """
        if not self.operations:
            self.logger.info("No operations to execute in batch")
            return []
        
        self.logger.info(f"Executing batch with {len(self.operations)} operations")
        
        # Group operations by type and customer ID
        grouped_operations = {}
        for operation in self.operations:
            key = (operation.operation_type.value, operation.customer_id)
            if key not in grouped_operations:
                grouped_operations[key] = []
            grouped_operations[key].append(operation)
        
        # Process each group
        results = []
        
        for (op_type, customer_id), operations in grouped_operations.items():
            self.logger.info(f"Processing batch of {len(operations)} {op_type} operations for customer {customer_id}")
            
            # Split into manageable chunks (max_batch_size)
            chunks = [operations[i:i + self.max_batch_size] for i in range(0, len(operations), self.max_batch_size)]
            
            for chunk_idx, chunk in enumerate(chunks):
                self.logger.info(f"Processing chunk {chunk_idx + 1} of {len(chunks)} with {len(chunk)} operations")
                
                # Group by operation type
                typed_operations = {}
                for op in chunk:
                    if op.operation_type not in typed_operations:
                        typed_operations[op.operation_type] = []
                    typed_operations[op.operation_type].append(op)
                
                # Process each operation type
                for op_type, ops in typed_operations.items():
                    try:
                        # Create API operations
                        api_operations = {}
                        
                        for op in ops:
                            created_op = self._create_operation(op)
                            if created_op:
                                service_method = created_op["method"]
                                if service_method not in api_operations:
                                    api_operations[service_method] = {
                                        "service": created_op["service"],
                                        "operations": [],
                                        "batch_ops": []
                                    }
                                api_operations[service_method]["operations"].append(created_op["operation"])
                                api_operations[service_method]["batch_ops"].append(op)
                        
                        # Execute each service method
                        for service_method, data in api_operations.items():
                            service = data["service"]
                            operations_list = data["operations"]
                            batch_ops = data["batch_ops"]
                            
                            self.logger.info(f"Executing {len(operations_list)} operations with {service_method}")
                            
                            # Get the service method and call it
                            service_method_func = getattr(service, service_method)
                            response = service_method_func(
                                customer_id=customer_id,
                                operations=operations_list,
                                partial_failure=True  # Enable partial failure mode
                            )
                            
                            # Process results
                            for i, result in enumerate(response.results):
                                op = batch_ops[i]
                                op.status = "COMPLETE"
                                op.result = {
                                    "resource_name": result.resource_name,
                                    "operation_id": op.operation_id,
                                    "operation_type": op.operation_type.value,
                                    "status": "SUCCESS"
                                }
                                results.append(op.result)
                            
                            # Check for partial failures
                            if response.partial_failure_error:
                                self.logger.warning(f"Batch operation had partial failures: {response.partial_failure_error}")
                                # Process partial failures if they exist
                                self._process_partial_failures(response.partial_failure_error, batch_ops, results)
                    
                    except GoogleAdsException as ex:
                        self.logger.error(f"Google Ads API error in batch operations: {ex}")
                        # Mark all operations in this group as failed
                        for op in ops:
                            op.status = "ERROR"
                            op.error = str(ex)
                            failed_result = {
                                "operation_id": op.operation_id,
                                "operation_type": op.operation_type.value,
                                "status": "ERROR",
                                "error": str(ex)
                            }
                            results.append(failed_result)
                    
                    except Exception as e:
                        self.logger.error(f"Unexpected error in batch operations: {e}")
                        # Mark all operations in this group as failed
                        for op in ops:
                            op.status = "ERROR"
                            op.error = str(e)
                            failed_result = {
                                "operation_id": op.operation_id,
                                "operation_type": op.operation_type.value,
                                "status": "ERROR",
                                "error": str(e)
                            }
                            results.append(failed_result)
                
                # Add a small delay between chunks to avoid rate limiting
                if len(chunks) > 1 and chunk_idx < len(chunks) - 1:
                    await asyncio.sleep(1)
        
        # Clear operations after execution
        self.operations = []
        
        return results
    
    def _process_partial_failures(self, partial_failure_error, operations, results):
        """
        Process partial failures in a batch operation.
        
        Args:
            partial_failure_error: The partial failure error from the API
            operations: The batch operations
            results: The results list to update
        """
        # In a real implementation, you would parse the partial_failure_error
        # to identify which operations failed and why
        # This is a simplified version
        self.logger.error(f"Partial failure in batch operation: {partial_failure_error}")
        
        # Mark all operations as failed for now
        # In a real implementation, you would only mark the failed operations
        for op in operations:
            # Check if this operation already has a success result
            if not any(r.get("operation_id") == op.operation_id and r.get("status") == "SUCCESS" for r in results):
                op.status = "ERROR"
                op.error = str(partial_failure_error)
                failed_result = {
                    "operation_id": op.operation_id,
                    "operation_type": op.operation_type.value,
                    "status": "ERROR",
                    "error": str(partial_failure_error)
                }
                results.append(failed_result)
        
    def clear(self):
        """Clear all operations in the batch."""
        self.operations = []
        self.logger.info("Batch operations cleared") 