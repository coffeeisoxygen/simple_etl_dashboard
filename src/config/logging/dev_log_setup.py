"""Development logging configuration."""

import sys
from pathlib import Path

from loguru import logger

from src.config.logging.log_state import LoggingState


def _create_log_directory() -> None:
    """Ensure logs directory exists."""
    Path("logs").mkdir(exist_ok=True)


def _get_terminal_format() -> str:
    """Get colorful format for terminal output."""
    return (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level:<8}</level> | "
        "<cyan>{name}</cyan>:<blue>{function}</blue>:<yellow>{line}</yellow> | "
        "<level>{message}</level>"
    )


def _get_file_format() -> str:
    """Get clean format for file logging."""
    return (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}"
    )


def _setup_terminal_handler() -> None:
    """Setup colorful terminal logging handler."""
    logger.add(
        sys.stderr,
        format=_get_terminal_format(),
        level="DEBUG",
        backtrace=True,
        diagnose=True,
        colorize=True,
        enqueue=True,
        catch=True,
    )


def _setup_app_log_handler() -> None:
    """Setup application log file handler."""
    logger.add(
        "logs/app.log",
        format=_get_file_format(),
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )


def _setup_error_log_handler() -> None:
    """Setup error-only log file handler."""
    logger.add(
        "logs/error.log",
        format=_get_file_format(),
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )


def setup_development_logging() -> bool:
    """Setup complete development logging configuration.

    Returns:
        True if successful, False otherwise
    """
    if LoggingState.is_dev_configured():
        return True

    try:
        # Remove default handler first
        logger.remove()

        # Setup directory and handlers
        _create_log_directory()
        _setup_terminal_handler()
        _setup_app_log_handler()
        _setup_error_log_handler()

        # Mark as configured
        LoggingState.mark_dev_configured()
        logger.debug("Development logging configured successfully")
        return True

    except Exception as e:
        error_msg = f"Failed to setup development logging: {e}"
        LoggingState.add_error(error_msg)
        logger.error(error_msg)
        return False
