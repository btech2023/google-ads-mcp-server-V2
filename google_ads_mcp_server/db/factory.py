"""
Database Factory Module

This module provides factory functions for creating database instances.
It supports different database backends (SQLite, PostgreSQL) and handles
configuration-based selection of the appropriate implementation.
"""

import os
import logging
from typing import Dict, Any, Optional

from .interface import DatabaseInterface

logger = logging.getLogger(__name__)

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
    if db_config is None:
        db_config = {}
    
    # Apply default values
    if db_type == "sqlite":
        if not SQLITE_AVAILABLE:
            raise ImportError("SQLite database manager is not available")
        
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
            raise ImportError("PostgreSQL database manager is not available. Please install required packages.")
        
        # Default PostgreSQL configuration
        if 'host' not in db_config:
            db_config['host'] = 'localhost'
        
        if 'port' not in db_config:
            db_config['port'] = 5432
        
        # Required parameters for PostgreSQL
        required_params = ['database', 'user', 'password']
        missing_params = [param for param in required_params if param not in db_config]
        
        if missing_params:
            raise ValueError(f"Missing required PostgreSQL configuration parameters: {', '.join(missing_params)}")
        
        logger.info(f"Creating PostgreSQL database manager for database: {db_config['database']} on host: {db_config['host']}")
        return PostgreSQLDatabaseManager(**db_config)
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}. Supported types are 'sqlite' and 'postgres'.") 