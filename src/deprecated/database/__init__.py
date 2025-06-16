"""Simplified database package API - Essential Operations Only.

Philosophy: KISS principle, focus on 6 core requirements:
1. Proper database system
2. Essential utilities without over-engineering
3. Admin seeding
4. Streamlit re-run safety
5. Database reset capability
6. Safe CRUD operations
"""

from src.database.database_service import DatabaseService, get_database_service
from src.database.db_config import DatabaseConfig
from src.database.db_exceptions import (
    ConnectionError,
    DatabaseError,
    QueryError,
    SchemaError,
)
from src.database.db_schema import DatabaseSchema

# Public API exports - simplified
__all__ = [
    # Core service
    "DatabaseService",
    "get_database_service",
    # Configuration
    "DatabaseConfig",
    "DatabaseSchema",
    # Exceptions
    "DatabaseError",
    "ConnectionError",
    "QueryError",
    "SchemaError",
]

# TODO: Add simple migration utilities if needed
# REMINDER: Keep it simple - no over-engineering!
