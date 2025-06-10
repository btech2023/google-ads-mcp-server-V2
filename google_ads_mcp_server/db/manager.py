"""Database manager compatibility layer."""

# flake8: noqa

from .sqlite_manager import SQLiteDatabaseManager as SQLiteDatabaseManager, SQLiteDatabaseManager as DatabaseManager

__all__ = ["SQLiteDatabaseManager", "DatabaseManager"]
