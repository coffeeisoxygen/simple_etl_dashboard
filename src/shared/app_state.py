"""Streamlit state management utilities for clean app lifecycle.

This module provides utilities for managing application state, one-time
initialization, and clean separation of concerns in Streamlit apps.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

import streamlit as st
from loguru import logger

# Type for generic functions
T = TypeVar("T")


class AppState:
    """Application state management utilities."""

    # State keys for common app components
    LOG_CONFIGURED = "is_log_configured"
    DATABASE_INITIALIZED = "is_database_initialized"
    USER_AUTHENTICATED = "user_authenticated"
    APP_READY = "app_ready"
    APP_INITIALIZED = "app_initialized"  # Added for complete app init

    @staticmethod
    def initialize_once(key: str, init_func: Callable[[], T]) -> T | None:
        """Initialize something once and store result in session state.

        This prevents re-initialization on Streamlit reruns while still
        allowing access to the initialization result.

        Args:
            key: Session state key to track initialization
            init_func: Function to call for initialization

        Returns:
            Result of init_func if first run, stored result otherwise
        """
        if key not in st.session_state:
            try:
                result = init_func()
                st.session_state[key] = result
                logger.debug(f"Initialized once: {key}")
                return result
            except Exception as e:
                logger.error(f"Failed to initialize {key}: {e}")
                # Store failure state to prevent repeated attempts
                st.session_state[key] = None
                return None

        return st.session_state[key]

    @staticmethod
    def ensure_initialized(key: str, init_func: Callable[[], bool]) -> bool:
        """Ensure one-time initialization for boolean state.

        Perfect for setup functions that return success/failure.

        Args:
            key: Session state key
            init_func: Function that returns True/False for success

        Returns:
            True if initialized successfully, False otherwise
        """
        if key not in st.session_state:
            logger.debug(f"Initializing: {key}")
            success = init_func()
            st.session_state[key] = success
            logger.debug(f"Initialization result for {key}: {success}")
            return success

        logger.debug(f"Already initialized: {key} = {st.session_state[key]}")
        return st.session_state[key]

    @staticmethod
    def get_state(key: str, default: Any = None) -> Any:
        """Get state value with optional default.

        Args:
            key: Session state key
            default: Default value if key doesn't exist

        Returns:
            State value or default
        """
        return st.session_state.get(key, default)

    @staticmethod
    def set_state(key: str, value: Any) -> None:
        """Set state value.

        Args:
            key: Session state key
            value: Value to set
        """
        st.session_state[key] = value

    @staticmethod
    def clear_state(key: str) -> None:
        """Clear specific state key.

        Args:
            key: Session state key to clear
        """
        if key in st.session_state:
            del st.session_state[key]

    @staticmethod
    def reset_app_state() -> None:
        """Reset all app-related state (useful for logout, etc.)."""
        keys_to_clear = [
            AppState.USER_AUTHENTICATED,
            AppState.APP_READY,
            # Keep LOG_CONFIGURED to avoid re-setup
            # Keep DATABASE_INITIALIZED to avoid re-setup
            # Keep APP_INITIALIZED to avoid re-setup
        ]

        for key in keys_to_clear:
            AppState.clear_state(key)

    @staticmethod
    def is_app_ready() -> bool:
        """Check if app is fully initialized and ready."""
        return all(
            [
                AppState.get_state(AppState.LOG_CONFIGURED, False),
                AppState.get_state(AppState.DATABASE_INITIALIZED, False),
            ]
        )


class AppInitializer:
    """Application initialization manager with proper state guards."""

    @staticmethod
    def setup_logging() -> bool:
        """Setup logging with guard against re-initialization."""
        from shared.log_setup import setup_smart_logging

        def _setup() -> bool:
            success = setup_smart_logging()
            if success:
                logger.info("Application logging initialized")
            return success

        return AppState.ensure_initialized(AppState.LOG_CONFIGURED, _setup)

    @staticmethod
    def setup_database() -> bool:
        """Setup database with guard against re-initialization."""
        from database import initialize_database

        def _setup() -> bool:
            try:
                success = initialize_database()
                if success:
                    logger.info("Database initialized successfully")
                else:
                    logger.error("Database initialization failed")
                return success
            except Exception as e:
                logger.error(f"Database initialization error: {e}")
                return False

        return AppState.ensure_initialized(AppState.DATABASE_INITIALIZED, _setup)

    @staticmethod
    def initialize_app() -> bool:
        """Initialize complete application stack with session state guard.

        This is the main guard that prevents re-initialization on reruns.

        Returns:
            True if all components initialized successfully
        """
        # MAIN GUARD: Check if already initialized
        if AppState.get_state(AppState.APP_INITIALIZED, False):
            logger.debug("App already initialized, skipping")
            return True

        logger.info("Starting application initialization...")
        success = True

        # Setup logging first (critical for debugging)
        if not AppInitializer.setup_logging():
            logger.error("Failed to setup logging")
            success = False

        # Setup database second
        if not AppInitializer.setup_database():
            logger.error("Failed to setup database")
            success = False

        # Mark components as ready if successful
        if success:
            AppState.set_state(AppState.APP_READY, True)
            AppState.set_state(
                AppState.APP_INITIALIZED, True
            )  # CRITICAL: Mark as initialized
            logger.info("Application initialization completed successfully")
        else:
            logger.error("Application initialization failed")

        return success


# Business-focused helper functions
def require_authentication(func: Callable) -> Callable:
    """Decorator to require authentication for page access.

    Usage:
        @require_authentication
        def protected_page():
            st.write("This page requires authentication")
    """

    def wrapper(*args, **kwargs):
        if not AppState.get_state(AppState.USER_AUTHENTICATED, False):
            st.error("Please login to access this page")
            st.stop()
        return func(*args, **kwargs)

    return wrapper


def get_user_context() -> dict[str, Any]:
    """Get current user context from session state."""
    return {
        "user_id": AppState.get_state("user_id"),
        "username": AppState.get_state("username"),
        "is_admin": AppState.get_state("is_admin", False),
        "authenticated": AppState.get_state(AppState.USER_AUTHENTICATED, False),
    }


def set_user_context(user_id: str, username: str, is_admin: bool = False) -> None:
    """Set user context in session state."""
    AppState.set_state("user_id", user_id)
    AppState.set_state("username", username)
    AppState.set_state("is_admin", is_admin)
    AppState.set_state(AppState.USER_AUTHENTICATED, True)


def clear_user_context() -> None:
    """Clear user context (logout)."""
    AppState.reset_app_state()
    logger.info("User logged out")


# Debug helpers for business owner
def show_state_debug() -> dict[str, Any]:
    """Get current state for debugging (business owner helper)."""
    return {
        "✅ Log Configured": AppState.get_state(AppState.LOG_CONFIGURED, False),
        "✅ Database Ready": AppState.get_state(AppState.DATABASE_INITIALIZED, False),
        "✅ App Initialized": AppState.get_state(AppState.APP_INITIALIZED, False),
        "✅ App Ready": AppState.get_state(AppState.APP_READY, False),
        "👤 User Authenticated": AppState.get_state(AppState.USER_AUTHENTICATED, False),
        "🔧 All Session Keys": list(st.session_state.keys()),
        "📊 Database Info": _get_database_debug_info(),
    }


def _get_database_debug_info() -> dict[str, Any]:
    """Get database debug information safely."""
    try:
        from database.streamlit_integration import get_db_session

        db = get_db_session()
        # Get database path from engine URL
        db_path = db.engine.url.database
        db_file = Path(db_path) if db_path else None

        return {
            "Database Path": str(db_path) if db_path else "Unknown",
            "File Exists": db_file.exists() if db_file else False,
            "File Size MB": round(db_file.stat().st_size / (1024 * 1024), 2)
            if db_file and db_file.exists()
            else 0,
            "Connection Healthy": db.engine is not None,
        }
    except Exception as e:
        return {"Database Error": str(e)}


# USAGE EXAMPLES:
# ===============

# # 1. Basic state management
# AppState.set_state('current_page', 'dashboard')
# current_page = AppState.get_state('current_page', 'home')
#
# # 2. One-time initialization
# def expensive_setup():
#     # Expensive operation here
#     return {"data": "loaded"}
#
# result = AppState.initialize_once('expensive_data', expensive_setup)
#
# # 3. Authentication requirement
# @require_authentication
# def admin_panel():
#     st.write("Admin only content")
#
# # 4. User context
# user = get_user_context()
# if user['authenticated']:
#     st.write(f"Welcome {user['username']}")
#
# # 5. Debug state (business owner)
# debug_info = show_state_debug()
