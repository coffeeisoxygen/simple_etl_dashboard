"""Clean file-based logging configuration - 3 handler strategy."""

import sys
from pathlib import Path
from typing import Any

from loguru import logger


class LoggingConfig:
    """File-based logging configuration manager."""

    # Log directories
    LOGS_DIR = Path("logs")

    # Log files
    APP_LOG_FILE = LOGS_DIR / "app.log"  # Development - all levels
    ERROR_LOG_FILE = LOGS_DIR / "error.log"  # Error - ERROR level only
    ACTIVITY_LOG_FILE = LOGS_DIR / "activity.log"  # Activity - business operations

    # Logging levels
    DEV_LEVEL = "DEBUG"
    ERROR_LEVEL = "ERROR"
    ACTIVITY_LEVEL = "INFO"

    # Rotation settings
    ROTATION_SIZE = "10 MB"
    RETENTION_DAYS = "30 days"
    ERROR_RETENTION_DAYS = "90 days"  # Keep errors longer

    # Format templates
    TERMINAL_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level:<8}</level> | "
        "<cyan>{name}</cyan>:<blue>{function}</blue>:<yellow>{line}</yellow> | "
        "<level>{message}</level>"
    )

    FILE_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}"
    )

    ACTIVITY_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {extra[action]:<12} | {message}"
    )

    @classmethod
    def ensure_log_directory(cls) -> None:
        """Ensure logs directory exists."""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_terminal_config(cls) -> dict[str, Any]:
        """Get terminal handler configuration."""
        return {
            "sink": sys.stderr,
            "format": cls.TERMINAL_FORMAT,
            "level": cls.DEV_LEVEL,
            "colorize": True,
            "backtrace": True,
            "diagnose": True,
            "enqueue": True,
            "catch": True,
        }

    @classmethod
    def get_app_log_config(cls) -> dict[str, Any]:
        """Get application log file handler configuration."""
        return {
            "sink": str(cls.APP_LOG_FILE),
            "format": cls.FILE_FORMAT,
            "level": cls.DEV_LEVEL,
            "rotation": cls.ROTATION_SIZE,
            "retention": cls.RETENTION_DAYS,
            "compression": "zip",
            "enqueue": True,
        }

    @classmethod
    def get_error_log_config(cls) -> dict[str, Any]:
        """Get error log file handler configuration."""
        return {
            "sink": str(cls.ERROR_LOG_FILE),
            "format": cls.FILE_FORMAT,
            "level": cls.ERROR_LEVEL,
            "rotation": cls.ROTATION_SIZE,
            "retention": cls.ERROR_RETENTION_DAYS,
            "compression": "gz",
            "enqueue": True,
        }

    @classmethod
    def get_activity_log_config(cls) -> dict[str, Any]:
        """Get activity log file handler configuration."""
        return {
            "sink": str(cls.ACTIVITY_LOG_FILE),
            "format": cls.ACTIVITY_FORMAT,
            "level": cls.ACTIVITY_LEVEL,
            "rotation": cls.ROTATION_SIZE,
            "retention": cls.RETENTION_DAYS,
            "compression": "zip",
            "filter": cls._activity_filter,
            "enqueue": True,
        }

    @classmethod
    def _activity_filter(cls, record: dict[str, Any]) -> bool:
        """Filter for activity log entries."""
        return "action" in record.get("extra", {})


def setup_logging() -> bool:
    """Setup complete file-based logging configuration.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Remove default handler
        logger.remove()

        # Ensure directory exists
        LoggingConfig.ensure_log_directory()

        # Add all handlers
        logger.add(**LoggingConfig.get_terminal_config())
        logger.add(**LoggingConfig.get_app_log_config())
        logger.add(**LoggingConfig.get_error_log_config())
        logger.add(**LoggingConfig.get_activity_log_config())

        logger.info("File-based logging configured successfully")
        return True

    except Exception as e:
        print(f"Failed to setup logging: {e}")  # Fallback to print
        return False


def log_activity(action: str, message: str, **kwargs) -> None:
    """Helper function for activity logging.

    Args:
        action: Business action being logged (e.g., 'IMPORT', 'LOGIN', 'CREATE')
        message: Log message
        **kwargs: Additional context data
    """
    logger.bind(action=action, **kwargs).info(message)


def get_activity_logger(action: str, **context) -> Any:
    """Get logger bound with activity context.

    Args:
        action: Primary action for this logger session
        **context: Additional context to bind

    Returns:
        Bound logger instance
    """
    return logger.bind(action=action, **context)


# NOTE :# Setup logging once at app startup
# from src.config.logging import setup_logging, log_activity

# # Initialize logging
# setup_logging()

# # Use in code
# log_activity("IMPORT", "CSV file imported successfully", file_name="data.csv", records=1000)

# # Or get context logger
# activity_logger = get_activity_logger("ETL_PROCESS", user_id="user123")
# activity_logger.info("Processing batch 1")
