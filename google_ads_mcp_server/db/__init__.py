"""
Database Package

This package provides database functionality for the Google Ads MCP Server,
including caching and persistent storage.
"""

from .interface import DatabaseInterface, DatabaseError
from .factory import get_database_manager

# Import the SQLite implementation for backward compatibility
# with code that directly imports DatabaseManager
from .sqlite_manager import SQLiteDatabaseManager as DatabaseManager

__all__ = [
    'DatabaseInterface', 
    'DatabaseError',
    'get_database_manager',
    'DatabaseManager'  # For backward compatibility
]
