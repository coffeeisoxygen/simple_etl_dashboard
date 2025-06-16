"""Database package with clean exports for easy importing."""

from .init import get_session_manager, initialize_database
from .session import SessionManager
from .streamlit_integration import get_db_session

# Business owner convenience exports
__all__ = [
    "initialize_database",  # Setup database
    "get_db_session",  # Get session manager for Streamlit
    "get_session_manager",  # Get session manager with custom path
    "SessionManager",  # Session manager class
]

# FUTURE: Add bulk operations when needed
# from .bulk_operations import BulkOperations
