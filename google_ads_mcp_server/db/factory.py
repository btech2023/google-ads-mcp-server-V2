"""
Database Factory Module

This module provides factory functions for creating database instances.
It supports different database backends (SQLite, PostgreSQL) and handles
configuration-based selection of the appropriate implementation.
"""

import os
from typing import Dict, Any, Optional

# Import utility modules
# Use absolute import from the project root
from google_ads_mcp_server.utils.error_handler import (
    handle_exception,
    SEVERITY_ERROR,
    CATEGORY_DATABASE
)
from google_ads_mcp_server.utils.validation import (
    validate_non_empty_string,
    validate_enum
)
from google_ads_mcp_server.utils.logging import get_logger

from .interface import DatabaseInterface

# Get logger
logger = get_logger(__name__)

# Import implementations when available
try:
    from .sqlite_manager import SQLiteDatabaseManager
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False
    logger.warning("SQLite database manager not available")

try:
    from .postgres_manager import PostgreSQLDatabaseManager
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.debug("PostgreSQL database manager not available. This is expected in development.")


def get_database_manager(
    db_type: str = "sqlite",
    db_config: Optional[Dict[str, Any]] = None
) -> DatabaseInterface:
    """
    Get a database manager instance based on the specified type and configuration.
    
    Args:
        db_type: The type of database to use ('sqlite' or 'postgres')
        db_config: Configuration parameters for the database
            For SQLite:
                - db_path: Path to the SQLite database file
                - auto_clean_interval: Interval between cache cleaning operations
            For PostgreSQL:
                - host: Database host
                - port: Database port
                - database: Database name
                - user: Database user
                - password: Database password
                - ssl_mode: SSL mode for connection
                - pool_min_size: Minimum connection pool size
                - pool_max_size: Maximum connection pool size
    
    Returns:
        A database manager instance implementing the DatabaseInterface
    
    Raises:
        ValueError: If the specified database type is not supported
        ImportError: If the required database implementation is not available
    """
    try:
        # Validate inputs
        validation_errors = []
        validate_non_empty_string(db_type, "db_type", validation_errors)
        validate_enum(db_type, "db_type", ["sqlite", "postgres"], validation_errors)
        
        if validation_errors:
            error_message = f"Validation errors in get_database_manager: {'; '.join(validation_errors)}"
            logger.error(error_message)
            raise ValueError(error_message)
            
        if db_config is None:
            db_config = {}
        
        # Apply default values
        if db_type == "sqlite":
            if not SQLITE_AVAILABLE:
                error_message = "SQLite database manager is not available"
                logger.error(error_message)
                raise ImportError(error_message)
            
            # Default SQLite configuration
            if 'db_path' not in db_config:
                # Default to a database file in the same directory as this module
                base_dir = os.path.dirname(os.path.abspath(__file__))
                db_config['db_path'] = os.path.join(base_dir, 'google_ads_mcp.db')
            
            if 'auto_clean_interval' not in db_config:
                db_config['auto_clean_interval'] = 3600  # 1 hour
            
            logger.info(f"Creating SQLite database manager with path: {db_config['db_path']}")
            return SQLiteDatabaseManager(**db_config)
        
        elif db_type == "postgres":
            if not POSTGRES_AVAILABLE:
                error_message = "PostgreSQL database manager is not available. Please install required packages."
                logger.error(error_message)
                raise ImportError(error_message)
            
            # Default PostgreSQL configuration
            if 'host' not in db_config:
                db_config['host'] = 'localhost'
            
            if 'port' not in db_config:
                db_config['port'] = 5432
            
            # Required parameters for PostgreSQL
            required_params = ['database', 'user', 'password']
            missing_params = [param for param in required_params if param not in db_config]
            
            if missing_params:
                error_message = f"Missing required PostgreSQL configuration parameters: {', '.join(missing_params)}"
                logger.error(error_message)
                raise ValueError(error_message)
            
            logger.info(f"Creating PostgreSQL database manager for database: {db_config['database']} on host: {db_config['host']}")
            return PostgreSQLDatabaseManager(**db_config)
    except Exception as e:
        # Handle exception with proper context
        error_details = handle_exception(
            e,
            context={"db_type": db_type, "config_keys": list(db_config.keys()) if db_config else []},
            severity=SEVERITY_ERROR,
            category=CATEGORY_DATABASE
        )
        logger.error(f"Failed to create database manager: {error_details.message}")
        raise ValueError(f"Database manager creation failed: {str(e)}") from e 