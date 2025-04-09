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

# Import utility modules
from ..utils.logging import get_logger
from ..utils.validation import (
    validate_customer_id,
    validate_positive_integer,
    validate_string_length,
    validate_enum,
    validate_list_not_empty
)
from ..utils.error_handler import (
    handle_exception,
    handle_google_ads_exception,
    create_error_response,
    ErrorDetails,
    CATEGORY_BUSINESS_LOGIC,
    CATEGORY_API_ERROR,
    CATEGORY_VALIDATION,
    SEVERITY_ERROR,
    SEVERITY_WARNING
)
from ..utils.formatting import clean_customer_id, format_customer_id

# Initialize logger using utility
logger = get_logger(__name__)

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
        logger.info("BatchManager initialized")

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
            ID of the added operation or error dictionary
        """
        context = {
            "operation_type": operation_type.value if operation_type else None,
            "operation_id": operation_id,
            "customer_id": customer_id,
            "method": "add_operation"
        }

        try:
            # Validation
            validation_errors = []
            
            # Validate operation_type is a valid OperationType
            if not isinstance(operation_type, OperationType):
                validation_errors.append(f"Invalid operation_type: {operation_type}. Must be an OperationType enum.")
            
            # Validate operation_id
            if not validate_string_length(operation_id, min_length=1):
                validation_errors.append("operation_id must not be empty")
            
            # Validate operation_data is a dictionary
            if not isinstance(operation_data, dict) or not operation_data:
                validation_errors.append("operation_data must be a non-empty dictionary")
            
            # Validate customer_id
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer_id format: {customer_id}")
                
            # If validation errors found, raise ValueError
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
            
            # Clean customer_id
            cleaned_customer_id = clean_customer_id(customer_id)
            
            # Create and add operation
            operation = BatchOperation(operation_type, operation_id, operation_data, cleaned_customer_id)
            self.operations.append(operation)
            logger.info(f"Added {operation_type.value} operation with ID {operation_id} to batch for customer {format_customer_id(cleaned_customer_id)}")
            return operation_id
            
        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error adding operation to batch: {error_details.message}")
            raise ve
        except Exception as e:
            error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
            logger.error(f"Error adding operation to batch: {error_details.message}")
            raise RuntimeError(f"Failed to add operation to batch: {error_details.message}") from e
    
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
        context = {
            "budget_id": budget_id,
            "amount_micros": amount_micros,
            "customer_id": customer_id,
            "method": "add_campaign_budget_update"
        }
        
        try:
            # Validation
            validation_errors = []
            
            if not validate_string_length(budget_id, min_length=1):
                validation_errors.append("budget_id must not be empty")
            
            if not validate_positive_integer(amount_micros):
                validation_errors.append(f"amount_micros must be a positive integer: {amount_micros}")
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer_id format: {customer_id}")
                
            # If validation errors found, raise ValueError
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
                
            # Prepare operation data
            operation_data = {
                "budget_id": budget_id,
                "amount_micros": amount_micros,
            }
            
            # Add operation to batch
            return self.add_operation(
                operation_type=OperationType.CAMPAIGN_BUDGET,
                operation_id=f"budget_update_{budget_id}",
                operation_data=operation_data,
                customer_id=customer_id
            )
            
        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error adding budget update to batch: {error_details.message}")
            raise ve
        except Exception as e:
            error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
            logger.error(f"Error adding budget update to batch: {error_details.message}")
            raise RuntimeError(f"Failed to add budget update to batch: {error_details.message}") from e
    
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
        context = {
            "ad_group_id": ad_group_id,
            "updates": updates,
            "customer_id": customer_id,
            "method": "add_ad_group_update"
        }
        
        try:
            # Validation
            validation_errors = []
            
            if not validate_string_length(ad_group_id, min_length=1):
                validation_errors.append("ad_group_id must not be empty")
            
            if not isinstance(updates, dict) or not updates:
                validation_errors.append("updates must be a non-empty dictionary")
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer_id format: {customer_id}")
                
            # Validate specific update fields
            if updates:
                for field, value in updates.items():
                    if field == "status" and value not in ["ENABLED", "PAUSED", "REMOVED"]:
                        validation_errors.append(f"Invalid status value: {value}. Must be one of: ENABLED, PAUSED, REMOVED")
                    if field == "cpc_bid_micros" and not validate_positive_integer(value):
                        validation_errors.append(f"cpc_bid_micros must be a positive integer: {value}")
                
            # If validation errors found, raise ValueError
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
                
            # Prepare operation data
            operation_data = {
                "ad_group_id": ad_group_id,
                "updates": updates
            }
            
            # Add operation to batch
            return self.add_operation(
                operation_type=OperationType.AD_GROUP,
                operation_id=f"ad_group_update_{ad_group_id}",
                operation_data=operation_data,
                customer_id=customer_id
            )
            
        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error adding ad group update to batch: {error_details.message}")
            raise ve
        except Exception as e:
            error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
            logger.error(f"Error adding ad group update to batch: {error_details.message}")
            raise RuntimeError(f"Failed to add ad group update to batch: {error_details.message}") from e
    
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
        context = {
            "keyword_id": keyword_id,
            "updates": updates,
            "customer_id": customer_id,
            "method": "add_keyword_update"
        }
        
        try:
            # Validation
            validation_errors = []
            
            if not validate_string_length(keyword_id, min_length=1):
                validation_errors.append("keyword_id must not be empty")
            
            if not isinstance(updates, dict) or not updates:
                validation_errors.append("updates must be a non-empty dictionary")
            
            if not validate_customer_id(customer_id):
                validation_errors.append(f"Invalid customer_id format: {customer_id}")
                
            # Validate specific update fields
            if updates:
                for field, value in updates.items():
                    if field == "status" and value not in ["ENABLED", "PAUSED", "REMOVED"]:
                        validation_errors.append(f"Invalid status value: {value}. Must be one of: ENABLED, PAUSED, REMOVED")
                    if field == "cpc_bid_micros" and not validate_positive_integer(value):
                        validation_errors.append(f"cpc_bid_micros must be a positive integer: {value}")
                
            # If validation errors found, raise ValueError
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
                
            # Prepare operation data
            operation_data = {
                "keyword_id": keyword_id,
                "updates": updates
            }
            
            # Add operation to batch
            return self.add_operation(
                operation_type=OperationType.KEYWORD,
                operation_id=f"keyword_update_{keyword_id}",
                operation_data=operation_data,
                customer_id=customer_id
            )
            
        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error adding keyword update to batch: {error_details.message}")
            raise ve
        except Exception as e:
            error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
            logger.error(f"Error adding keyword update to batch: {error_details.message}")
            raise RuntimeError(f"Failed to add keyword update to batch: {error_details.message}") from e
    
    def _create_budget_operation(self, operation: BatchOperation) -> Dict[str, Any]:
        """
        Create a campaign budget operation.
        
        Args:
            operation: The batch operation
            
        Returns:
            Google Ads API operation object
        """
        try:
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
        except Exception as e:
            logger.error(f"Error creating budget operation: {str(e)}")
            raise
    
    def _create_ad_group_operation(self, operation: BatchOperation) -> Dict[str, Any]:
        """
        Create an ad group operation.
        
        Args:
            operation: The batch operation
            
        Returns:
            Google Ads API operation object
        """
        try:
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
        except Exception as e:
            logger.error(f"Error creating ad group operation: {str(e)}")
            raise
    
    def _create_keyword_operation(self, operation: BatchOperation) -> Dict[str, Any]:
        """
        Create a keyword operation.
        
        Args:
            operation: The batch operation
            
        Returns:
            Google Ads API operation object
        """
        try:
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
        except Exception as e:
            logger.error(f"Error creating keyword operation: {str(e)}")
            raise
    
    def _create_operation(self, operation: BatchOperation) -> Optional[Dict[str, Any]]:
        """
        Create a Google Ads API operation based on the operation type.
        
        Args:
            operation: The batch operation
            
        Returns:
            Google Ads API operation object, or None if the operation type is not supported
        """
        try:
            if operation.operation_type == OperationType.CAMPAIGN_BUDGET:
                return self._create_budget_operation(operation)
            elif operation.operation_type == OperationType.AD_GROUP:
                return self._create_ad_group_operation(operation)
            elif operation.operation_type == OperationType.KEYWORD:
                return self._create_keyword_operation(operation)
            else:
                logger.warning(f"Unsupported operation type: {operation.operation_type.value}")
                return None
        except Exception as e:
            logger.error(f"Error creating operation of type {operation.operation_type.value}: {str(e)}")
            raise
    
    async def execute_batch(self) -> List[Dict[str, Any]]:
        """
        Execute all operations in the batch.
        
        Returns:
            List of results for each operation
        """
        context = {"method": "execute_batch", "operation_count": len(self.operations)}
        
        try:
            # Validation
            if not self.operations:
                logger.info("No operations to execute in batch")
                return []
            
            if not validate_list_not_empty(self.operations):
                raise ValueError("No operations to execute in batch")
            
            logger.info(f"Executing batch with {len(self.operations)} operations")
            
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
                logger.info(f"Processing batch of {len(operations)} {op_type} operations for customer {format_customer_id(customer_id)}")
                
                # Split into manageable chunks (max_batch_size)
                chunks = [operations[i:i + self.max_batch_size] for i in range(0, len(operations), self.max_batch_size)]
                
                for chunk_idx, chunk in enumerate(chunks):
                    logger.info(f"Processing chunk {chunk_idx + 1} of {len(chunks)} with {len(chunk)} operations")
                    
                    # Group by operation type
                    typed_operations = {}
                    for op in chunk:
                        if op.operation_type not in typed_operations:
                            typed_operations[op.operation_type] = []
                        typed_operations[op.operation_type].append(op)
                    
                    # Process each operation type
                    for op_type, ops in typed_operations.items():
                        chunk_context = {
                            "operation_type": op_type.value,
                            "customer_id": customer_id,
                            "chunk_index": chunk_idx + 1,
                            "operation_count": len(ops),
                            "method": "execute_batch"
                        }
                        
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
                                
                                logger.info(f"Executing {len(operations_list)} operations with {service_method}")
                                
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
                                    logger.warning(f"Batch operation had partial failures: {response.partial_failure_error}")
                                    # Process partial failures if they exist
                                    self._process_partial_failures(response.partial_failure_error, batch_ops, results)
                        
                        except GoogleAdsException as ex:
                            # Handle Google Ads API exceptions specifically
                            error_details = handle_google_ads_exception(ex, context=chunk_context)
                            logger.error(f"Google Ads API error in batch operations: {error_details.message}")
                            
                            # Mark all operations in this group as failed
                            for op in ops:
                                op.status = "ERROR"
                                op.error = error_details.message
                                failed_result = {
                                    "operation_id": op.operation_id,
                                    "operation_type": op.operation_type.value,
                                    "status": "ERROR",
                                    "error": error_details.message
                                }
                                results.append(failed_result)
                        
                        except Exception as e:
                            # Handle other exceptions
                            error_details = handle_exception(e, context=chunk_context, category=CATEGORY_BUSINESS_LOGIC)
                            logger.error(f"Unexpected error in batch operations: {error_details.message}")
                            
                            # Mark all operations in this group as failed
                            for op in ops:
                                op.status = "ERROR"
                                op.error = error_details.message
                                failed_result = {
                                    "operation_id": op.operation_id,
                                    "operation_type": op.operation_type.value,
                                    "status": "ERROR",
                                    "error": error_details.message
                                }
                                results.append(failed_result)
                    
                    # Add a small delay between chunks to avoid rate limiting
                    if len(chunks) > 1 and chunk_idx < len(chunks) - 1:
                        await asyncio.sleep(1)
            
            # Clear operations after execution
            self.operations = []
            
            logger.info(f"Batch execution complete, {len(results)} operations processed")
            return results
            
        except ValueError as ve:
            error_details = handle_exception(ve, context=context, severity=SEVERITY_WARNING, category=CATEGORY_VALIDATION)
            logger.warning(f"Validation error executing batch: {error_details.message}")
            raise ve
        except Exception as e:
            error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
            logger.error(f"Error executing batch: {error_details.message}")
            raise RuntimeError(f"Failed to execute batch: {error_details.message}") from e
    
    def _process_partial_failures(self, partial_failure_error, operations, results):
        """
        Process partial failures in a batch operation.
        
        Args:
            partial_failure_error: The partial failure error from the API
            operations: The batch operations
            results: The results list to update
        """
        context = {
            "error": str(partial_failure_error),
            "method": "_process_partial_failures"
        }
        
        try:
            # In a real implementation, you would parse the partial_failure_error
            # to identify which operations failed and why
            # This is a simplified version
            error_details = handle_exception(
                partial_failure_error, 
                context=context, 
                category=CATEGORY_API_ERROR
            )
            logger.error(f"Partial failure in batch operation: {error_details.message}")
            
            # Mark all operations as failed for now
            # In a real implementation, you would only mark the failed operations
            for op in operations:
                # Check if this operation already has a success result
                if not any(r.get("operation_id") == op.operation_id and r.get("status") == "SUCCESS" for r in results):
                    op.status = "ERROR"
                    op.error = error_details.message
                    failed_result = {
                        "operation_id": op.operation_id,
                        "operation_type": op.operation_type.value,
                        "status": "ERROR",
                        "error": error_details.message
                    }
                    results.append(failed_result)
        except Exception as e:
            # Handle unexpected errors during partial failure processing
            error_details = handle_exception(e, context=context, category=CATEGORY_BUSINESS_LOGIC)
            logger.error(f"Error processing partial failures: {error_details.message}")
        
    def clear(self):
        """Clear all operations in the batch."""
        self.operations = []
        logger.info("Batch operations cleared") 