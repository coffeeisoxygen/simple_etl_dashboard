"""Streamlit integration for database services."""

from pathlib import Path

import streamlit as st

from .init import get_session_manager
from .session import SessionManager


@st.cache_resource
def get_cached_session_manager(db_path: str | None = None) -> SessionManager:
    """Get cached session manager for Streamlit.

    Args:
        db_path: Optional database path as string

    Returns:
        Cached SessionManager instance
    """
    path = Path(db_path) if db_path else None
    return get_session_manager(path)


# Business owner convenience function
def get_db_session() -> SessionManager:
    """Get database session manager - simple shortcut."""
    return get_cached_session_manager()
