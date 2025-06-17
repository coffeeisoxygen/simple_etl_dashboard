"""Database module for ETL Dashboard.

Single source of truth for all database operations.
"""

from .database import (
    # Advanced (if needed)
    StreamlitSQLManager,
    check_database_health,
    create_tables,
    execute_write,
    get_database_status,
    get_session,
    get_sql_manager,
    initialize_database,
    query_data,
)

__all__ = [
    "get_sql_manager",
    "initialize_database",
    "get_database_status",
    "get_session",
    "query_data",
    "execute_write",
    "check_database_health",
    "StreamlitSQLManager",
    "create_tables",
]
