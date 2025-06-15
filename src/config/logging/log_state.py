"""Centralized logging state management."""

from typing import Any

import streamlit as st


class LoggingState:
    """State management for logging configuration."""

    # State keys - using descriptive constants
    DEV_LOG_KEY = "development_log_configured"
    AUDIT_LOG_KEY = "audit_log_configured"
    LOG_ERRORS_KEY = "logging_setup_errors"

    @classmethod
    def is_dev_configured(cls) -> bool:
        """Check if development logging is configured."""
        return st.session_state.get(cls.DEV_LOG_KEY, False)

    @classmethod
    def is_audit_configured(cls) -> bool:
        """Check if audit logging is configured."""
        return st.session_state.get(cls.AUDIT_LOG_KEY, False)

    @classmethod
    def is_fully_configured(cls) -> bool:
        """Check if all logging components are configured."""
        return cls.is_dev_configured() and cls.is_audit_configured()

    @classmethod
    def mark_dev_configured(cls) -> None:
        """Mark development logging as configured."""
        st.session_state[cls.DEV_LOG_KEY] = True

    @classmethod
    def mark_audit_configured(cls) -> None:
        """Mark audit logging as configured."""
        st.session_state[cls.AUDIT_LOG_KEY] = True

    @classmethod
    def add_error(cls, error: str) -> None:
        """Add logging setup error to state."""
        if cls.LOG_ERRORS_KEY not in st.session_state:
            st.session_state[cls.LOG_ERRORS_KEY] = []
        st.session_state[cls.LOG_ERRORS_KEY].append(error)

    @classmethod
    def get_errors(cls) -> list[str]:
        """Get all logging setup errors."""
        return st.session_state.get(cls.LOG_ERRORS_KEY, [])

    @classmethod
    def clear_errors(cls) -> None:
        """Clear all logging setup errors."""
        if cls.LOG_ERRORS_KEY in st.session_state:
            del st.session_state[cls.LOG_ERRORS_KEY]

    @classmethod
    def get_status(cls) -> dict[str, Any]:
        """Get comprehensive logging status."""
        return {
            "dev_configured": cls.is_dev_configured(),
            "audit_configured": cls.is_audit_configured(),
            "fully_configured": cls.is_fully_configured(),
            "errors": cls.get_errors(),
            "error_count": len(cls.get_errors()),
        }

    @classmethod
    def reset_state(cls) -> None:
        """Reset all logging state - useful for testing."""
        keys_to_remove = [cls.DEV_LOG_KEY, cls.AUDIT_LOG_KEY, cls.LOG_ERRORS_KEY]

        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
