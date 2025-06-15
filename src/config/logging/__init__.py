"""Logging package - unified interface for all logging functionality."""

from typing import Any

from src.config.logging.audit_config import (
    get_audit_context,
    get_audit_logger,
    log_action,
)
from src.config.logging.audit_log_setup import get_audit_status, setup_audit_logging
from src.config.logging.dev_log_setup import setup_development_logging
from src.config.logging.log_state import LoggingState

__all__ = [
    # State management
    "LoggingState",
    # Setup functions
    "setup_development_logging",
    "setup_audit_logging",
    "setup_logging",
    "get_logging_status",
    "reset_logging_state",
    # Audit logging interface
    "get_audit_logger",
    "get_audit_context",
    "log_action",
    "get_audit_status",
]


def setup_logging() -> dict[str, Any]:
    """Setup complete logging configuration.

    This is the main entry point for logging setup.

    Returns:
        Dictionary with setup status for each logging component
    """
    if LoggingState.is_fully_configured():
        return {"development": True, "audit": True, "success": True}

    # Clear previous errors before setup
    LoggingState.clear_errors()

    # Setup both logging systems
    dev_success = setup_development_logging()
    audit_success = setup_audit_logging()

    # Import here to avoid circular import after loguru is configured
    from loguru import logger

    # Log completion status
    if dev_success and audit_success:
        logger.info("Complete logging configuration successful")
    else:
        errors = LoggingState.get_errors()
        logger.warning(f"Logging setup completed with errors: {errors}")

    return {
        "development": dev_success,
        "audit": audit_success,
        "success": dev_success and audit_success,
        "errors": LoggingState.get_errors(),
    }


def get_logging_status() -> dict[str, Any]:
    """Get current logging configuration status.

    Returns:
        Comprehensive status dictionary
    """
    status = LoggingState.get_status()
    audit_status = get_audit_status()

    return {**status, "audit_available": audit_status["available"]}


def reset_logging_state() -> None:
    """Reset logging state - useful for testing or reconfiguration."""
    LoggingState.reset_state()

    # Import here to avoid issues if logging not configured
    try:
        from loguru import logger

        logger.info("Logging state reset completed")
    except Exception:
        pass  # If logging not configured, that's fine
