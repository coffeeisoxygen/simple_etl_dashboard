"""Audit logging setup and configuration."""

from loguru import logger

from src.config.logging.audit_config import get_audit_logger
from src.config.logging.log_state import LoggingState


def setup_audit_logging() -> bool:
    """Setup audit logging configuration.

    Returns:
        True if successful, False otherwise
    """
    if LoggingState.is_audit_configured():
        return True

    try:
        # Initialize audit logger (this sets up database and sink)
        get_audit_logger()

        # Mark as configured
        LoggingState.mark_audit_configured()
        logger.debug("Audit logging configured successfully")
        return True

    except Exception as e:
        error_msg = f"Failed to setup audit logging: {e}"
        LoggingState.add_error(error_msg)
        logger.error(error_msg)
        return False


def get_audit_status() -> dict[str, bool]:
    """Get audit logging status details.

    Returns:
        Dictionary with audit logging status information
    """
    return {
        "configured": LoggingState.is_audit_configured(),
        "available": True,  # Audit logging is always available
    }
