"""Enhanced logging configuration with environment awareness and Streamlit integration.

This module provides intelligent logging setup that automatically configures
appropriate handlers based on environment and usage context.

Environment Detection:
- Development: Terminal + minimal file logging
- Production: Full file logging + rotation
- Testing: Terminal only

Handler Flow:
- Terminal: Always for development visibility
- App Log: Complete application flow
- Error Log: Critical issues only
- Activity Log: Business operations tracking
- Performance Log: ETL timing and metrics
- Streamlit Log: Framework-specific issues
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Literal

from loguru import logger

# Environment detection
Environment = Literal["development", "production", "testing"]


def detect_environment() -> Environment:
    """Detect current runtime environment.

    Returns:
        Environment type based on various indicators
    """
    # Check explicit environment variable
    env = os.getenv("APP_ENV", "").lower()
    if env in ["production", "prod"]:
        return "production"
    if env in ["testing", "test"]:
        return "testing"

    # Check if running in pytest
    if "pytest" in sys.modules:
        return "testing"

    # Check if running as packaged app (for distribution)
    if getattr(sys, "frozen", False):
        return "production"

    # Default to development
    return "development"


class StreamlitInterceptHandler(logging.Handler):
    """Intercept standard logging messages and route to Loguru.

    This handler captures logs from Streamlit and third-party libraries,
    filtering out noise while preserving important messages.
    """

    # Modules to reduce logging noise from
    NOISY_MODULES = {
        "streamlit.runtime.caching",
        "streamlit.runtime.state",
        "streamlit.runtime.legacy_caching",
        "watchdog.observers",
        "tornado.access",
        "urllib3.connectionpool",
        "asyncio",
    }

    def emit(self, record: logging.LogRecord) -> None:
        """Route standard logging record through Loguru."""
        try:
            # Skip noisy modules unless it's a warning/error
            if self._should_filter_out(record):
                return

            # Map level and emit through Loguru
            level = self._map_level(record.levelname)

            logger.bind(source=record.name, streamlit=True).opt(
                depth=6, exception=record.exc_info
            ).log(level, record.getMessage())

        except Exception:
            # Never let logging errors crash the app
            self.handleError(record)

    def _should_filter_out(self, record: logging.LogRecord) -> bool:
        """Determine if record should be filtered out."""
        # Always keep warnings and errors
        if record.levelno >= logging.WARNING:
            return False

        # Filter out known noisy modules
        return record.name in self.NOISY_MODULES or any(
            record.name.startswith(module) for module in self.NOISY_MODULES
        )

    def _map_level(self, level_name: str) -> str:
        """Map standard logging level to Loguru level."""
        mapping = {
            "DEBUG": "DEBUG",
            "INFO": "INFO",
            "WARNING": "WARNING",
            "WARN": "WARNING",  # Some libraries use WARN
            "ERROR": "ERROR",
            "CRITICAL": "CRITICAL",
        }
        return mapping.get(level_name, level_name)


class SmartLoggingConfig:
    """Environment-aware logging configuration with clear handler routing."""

    # Directories
    LOGS_DIR = Path("logs")

    # Core log files
    APP_LOG_FILE = LOGS_DIR / "app.log"
    ERROR_LOG_FILE = LOGS_DIR / "error.log"
    ACTIVITY_LOG_FILE = LOGS_DIR / "activity.log"

    # Enhanced log files
    PERFORMANCE_LOG_FILE = LOGS_DIR / "performance.log"
    STREAMLIT_LOG_FILE = LOGS_DIR / "streamlit.log"

    # Rotation settings per environment
    ROTATION_SETTINGS = {
        "development": {
            "size": "5 MB",
            "retention": "7 days",
        },
        "production": {
            "size": "50 MB",
            "retention": "90 days",
        },
        "testing": {
            "size": "1 MB",
            "retention": "1 day",
        },
    }

    # Logging formats
    TERMINAL_FORMAT = (
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level:<8}</level> | "
        "<cyan>{name}</cyan>:<blue>{function}-{line}</blue> | "
        "<level>{message}</level>"
    )

    FILE_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}"
    )

    ACTIVITY_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {extra[action]:<15} | {message}"
    )

    PERFORMANCE_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | "
        "{extra[operation]:<20} | {extra[duration]:<10} | {message}"
    )

    def __init__(self, environment: Environment):
        """Initialize with environment-specific settings."""
        self.environment = environment
        self.rotation_config = self.ROTATION_SETTINGS[environment]

    @classmethod
    def ensure_log_directory(cls) -> None:
        """Ensure logs directory exists."""
        cls.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def get_active_handlers(self) -> list[str]:
        """Get list of handlers that should be active for current environment.

        Returns:
            List of handler names to activate
        """
        handlers = ["terminal"]  # Terminal always active for visibility

        if self.environment == "development":
            handlers.extend(["app_log", "error_log"])  # Minimal file logging

        elif self.environment == "production":
            handlers.extend(
                [
                    "app_log",
                    "error_log",
                    "activity_log",
                    "performance_log",
                    "streamlit_log",
                ]
            )  # Full logging suite

        elif self.environment == "testing":
            # Terminal only for testing
            pass

        return handlers

    def get_terminal_config(self) -> dict[str, Any]:
        """Terminal handler - always active for development visibility."""
        return {
            "sink": sys.stderr,
            "format": self.TERMINAL_FORMAT,
            "level": "DEBUG" if self.environment == "development" else "INFO",
            "colorize": True,
            "backtrace": self.environment == "development",
            "diagnose": self.environment == "development",
            "enqueue": True,
        }

    def get_app_log_config(self) -> dict[str, Any]:
        """App log handler - complete application flow."""
        return {
            "sink": str(self.APP_LOG_FILE),
            "format": self.FILE_FORMAT,
            "level": "DEBUG",
            "rotation": self.rotation_config["size"],
            "retention": self.rotation_config["retention"],
            "compression": "zip",
            "enqueue": True,
            "filter": lambda record: not record.get("extra", {}).get(
                "streamlit", False
            ),
        }

    def get_error_log_config(self) -> dict[str, Any]:
        """Error log handler - critical issues only."""
        return {
            "sink": str(self.ERROR_LOG_FILE),
            "format": self.FILE_FORMAT,
            "level": "ERROR",
            "rotation": self.rotation_config["size"],
            "retention": "180 days",  # Keep errors longer
            "compression": "gz",
            "enqueue": True,
        }

    def get_activity_log_config(self) -> dict[str, Any]:
        """Activity log handler - business operations tracking."""
        return {
            "sink": str(self.ACTIVITY_LOG_FILE),
            "format": self.ACTIVITY_FORMAT,
            "level": "INFO",
            "rotation": self.rotation_config["size"],
            "retention": self.rotation_config["retention"],
            "compression": "zip",
            "filter": lambda record: "action" in record.get("extra", {}),
            "enqueue": True,
        }

    def get_performance_log_config(self) -> dict[str, Any]:
        """Performance log handler - ETL timing and metrics."""
        return {
            "sink": str(self.PERFORMANCE_LOG_FILE),
            "format": self.PERFORMANCE_FORMAT,
            "level": "INFO",
            "rotation": self.rotation_config["size"],
            "retention": self.rotation_config["retention"],
            "compression": "zip",
            "filter": lambda record: "operation" in record.get("extra", {}),
            "enqueue": True,
        }

    def get_streamlit_log_config(self) -> dict[str, Any]:
        """Streamlit log handler - framework-specific issues."""
        return {
            "sink": str(self.STREAMLIT_LOG_FILE),
            "format": self.FILE_FORMAT,
            "level": "WARNING",  # Only warnings and errors from Streamlit
            "rotation": self.rotation_config["size"],
            "retention": "30 days",  # Shorter retention
            "compression": "zip",
            "filter": lambda record: record.get("extra", {}).get("streamlit", False),
            "enqueue": True,
        }

    def setup_streamlit_intercept(self) -> None:
        """Setup interception of standard logging to route through Loguru."""
        # Only setup if we're actually using Streamlit handlers
        if "streamlit_log" not in self.get_active_handlers():
            return

        # Get root logger and clear existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        # Add our intercept handler
        intercept_handler = StreamlitInterceptHandler()
        root_logger.addHandler(intercept_handler)
        root_logger.setLevel(logging.DEBUG)

        # Configure specific noisy loggers
        noisy_loggers = ["streamlit", "tornado", "urllib3", "watchdog", "asyncio"]

        for logger_name in noisy_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)


def setup_smart_logging(environment: Environment | None = None) -> bool:
    """Setup intelligent logging based on environment.

    This function automatically detects the environment and configures
    appropriate logging handlers. Clear documentation of what goes where.

    Handler Flow Documentation:
    ---------------------------
    Development Environment:
        ✅ Terminal: All logs (DEBUG level) - immediate feedback
        ✅ App Log: Complete flow - debugging and tracing
        ✅ Error Log: Critical issues - problem solving
        ❌ Activity/Performance/Streamlit: Minimal noise

    Production Environment:
        ✅ Terminal: INFO+ only - operational visibility
        ✅ App Log: Complete application flow
        ✅ Error Log: Critical issues with long retention
        ✅ Activity Log: Business operations tracking
        ✅ Performance Log: ETL metrics and timing
        ✅ Streamlit Log: Framework issues

    Testing Environment:
        ✅ Terminal: Test output only
        ❌ File Logs: No file pollution during tests

    Args:
        environment: Force specific environment, auto-detect if None

    Returns:
        True if successful, False otherwise
    """
    try:
        # Detect environment if not specified
        if environment is None:
            environment = detect_environment()

        # Remove default Loguru handler
        logger.remove()

        # Create config for detected environment
        config = SmartLoggingConfig(environment)

        # Ensure directory exists (except for testing)
        if environment != "testing":
            config.ensure_log_directory()

        # Get active handlers for this environment
        active_handlers = config.get_active_handlers()

        # Setup handlers based on environment
        handler_methods = {
            "terminal": config.get_terminal_config,
            "app_log": config.get_app_log_config,
            "error_log": config.get_error_log_config,
            "activity_log": config.get_activity_log_config,
            "performance_log": config.get_performance_log_config,
            "streamlit_log": config.get_streamlit_log_config,
        }

        # Add only active handlers
        for handler_name in active_handlers:
            if handler_name in handler_methods:
                logger.add(**handler_methods[handler_name]())

        # Setup Streamlit interception if needed
        config.setup_streamlit_intercept()

        # Log successful setup with environment info
        logger.info(
            f"Smart logging configured for {environment} environment "
            f"(handlers: {', '.join(active_handlers)})"
        )

        return True

    except Exception as e:
        print(f"Failed to setup smart logging: {e}")
        return False


# Business-focused helper functions
def log_activity(action: str, message: str, **kwargs) -> None:
    """Log business activity with clear action tracking.

    Args:
        action: Business action (e.g., 'CSV_IMPORT', 'USER_LOGIN', 'DATA_EXPORT')
        message: Descriptive message
        **kwargs: Additional context (user_id, file_name, record_count, etc.)
    """
    logger.bind(action=action, **kwargs).info(message)


def log_performance(operation: str, duration: float, message: str, **kwargs) -> None:
    """Log performance metrics for ETL operations.

    Args:
        operation: Operation name (e.g., 'CSV_PARSE', 'DB_INSERT', 'DATA_TRANSFORM')
        duration: Duration in seconds
        message: Descriptive message
        **kwargs: Additional metrics (record_count, file_size, etc.)
    """
    logger.bind(operation=operation, duration=f"{duration:.3f}s", **kwargs).info(
        message
    )


def get_business_logger(context: str, **bindings) -> Any:
    """Get logger with business context bound.

    Args:
        context: Business context (e.g., 'ETL_PIPELINE', 'USER_MGMT', 'REPORTING')
        **bindings: Context to bind to logger

    Returns:
        Bound logger instance
    """
    return logger.bind(context=context, **bindings)


# Performance logging decorator
def log_etl_operation(operation_name: str):  # noqa: ANN201
    """Decorator to automatically log ETL operations with timing.

    Usage:
        @log_etl_operation("CSV_IMPORT")
        def import_csv_file(file_path: str):
            # Your implementation
            pass
    """

    def decorator(func):  # noqa: ANN001, ANN202
        import time
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):  # noqa: ANN202
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                log_performance(
                    operation_name, duration, f"{operation_name} completed successfully"
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.bind(
                    operation=operation_name, duration=f"{duration:.3f}s"
                ).error(f"{operation_name} failed: {e}")
                raise

        return wrapper

    return decorator


# Environment detection helper
def get_current_environment() -> Environment:
    """Get current detected environment."""
    return detect_environment()


def is_development() -> bool:
    """Check if running in development environment."""
    return detect_environment() == "development"


def is_production() -> bool:
    """Check if running in production environment."""
    return detect_environment() == "production"


# USAGE EXAMPLES:
# ===============

# # 1. Setup at app startup (automatic environment detection)
# from src.log_setup import setup_smart_logging, log_activity, log_performance
#
# # Initialize smart logging
# setup_smart_logging()
#
# # 2. Force specific environment
# setup_smart_logging("production")
#
# # 3. Business activity logging
# log_activity("APP_START", "ETL Dashboard starting up", version="1.0.0")
# log_activity("CSV_IMPORT", "Retailer data imported", file_size="2.3MB", records=1547)
#
# # 4. Performance logging
# log_performance("DB_QUERY", 0.045, "Retailer data query completed", records=1547)
#
# # 5. Decorator usage
# @log_etl_operation("TRANSACTION_IMPORT")
# def import_transactions(csv_file: str):
#     # Your logic here
#     pass
#
# # 6. Context logger
# etl_logger = get_business_logger("ETL_PIPELINE", batch_id="20250116_001")
# etl_logger.info("Starting batch processing")
