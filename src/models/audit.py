"""Simplified audit system menggunakan loguru dengan custom database sink."""

from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger

from src.models.commons import DatabaseEntity


class ActivityType(str, Enum):
    """Activity types untuk structured logging."""

    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    CSV_UPLOAD = "csv_upload"
    DATA_PROCESSING = "data_processing"
    PAGE_VIEW = "page_view"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_START = "system_start"


class AuditLog(DatabaseEntity):
    """Minimal audit log model untuk database persistence."""

    user_id: int | None = None
    session_id: str | None = None
    activity_type: str
    message: str
    details: dict[str, Any]
    level: str

    model_config = {
        "arbitrary_types_allowed": True,
    }


class AuditDatabaseSink:
    """Custom loguru sink untuk save audit logs ke database."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def __call__(self, message: Any) -> None:
        """Handle loguru message untuk audit database."""
        record = message.record
        extra = record.get("extra", {})

        # Only process audit logs
        if not extra.get("audit", False):
            return

        # Convert loguru record ke audit log
        audit_log = AuditLog(
            user_id=extra.get("user_id"),
            session_id=extra.get("session_id"),
            activity_type=extra.get("activity_type", "unknown"),
            message=record["message"],
            details=extra.get("details", {}),
            level=record["level"].name,
            act_date=record["time"].replace(tzinfo=None),  # Use act_date for log time
        )

        # Save via repository
        try:
            self.repository.save_audit_log(audit_log)
        except Exception as e:
            # Fallback logging - avoid recursive logging
            print(f"Failed to save audit log: {e}")


class AuditLogger:
    """Wrapper untuk audit logging dengan loguru."""

    def __init__(
        self, user_id: int | None = None, session_id: str | None = None
    ) -> None:
        self.base_context = {
            "audit": True,
            "user_id": user_id,
            "session_id": session_id,
        }
        self.logger = logger.bind(**self.base_context)

    def log_authentication(
        self, activity: str, success: bool, username: str, **details: Any
    ) -> None:
        """Log authentication activity."""
        message = f"Authentication {activity}: {'Success' if success else 'Failed'} for {username}"

        self.logger.bind(
            activity_type=ActivityType.LOGIN,
            details={"username": username, "success": success, **details},
        ).info(message)

    def log_data_activity(
        self,
        activity: str,
        filename: str | None = None,
        record_count: int | None = None,
        **details: Any,
    ) -> None:
        """Log data processing activity."""
        message = f"Data activity: {activity}"
        if filename:
            message += f" - {filename}"
        if record_count:
            message += f" ({record_count} records)"

        activity_details = {}
        if filename:
            activity_details["filename"] = filename
        if record_count:
            activity_details["record_count"] = record_count
        activity_details.update(details)

        self.logger.bind(
            activity_type=ActivityType.CSV_UPLOAD, details=activity_details
        ).info(message)

    def log_navigation(
        self, page: str, action: str | None = None, **details: Any
    ) -> None:
        """Log navigation activity."""
        message = f"Navigation: {page}"
        if action:
            message += f" - {action}"

        nav_details = {"page": page}
        if action:
            nav_details["action"] = action
        nav_details.update(details)

        self.logger.bind(
            activity_type=ActivityType.PAGE_VIEW, details=nav_details
        ).info(message)

    def log_error(
        self,
        error_message: str,
        error_type: str | None = None,
        stack_trace: str | None = None,
        **details: Any,
    ) -> None:
        """Log error dengan context."""
        context_details = {"error_type": error_type}
        if stack_trace:
            context_details["stack_trace"] = stack_trace
        context_details.update(details)

        self.logger.bind(
            activity_type=ActivityType.ERROR_OCCURRED, details=context_details
        ).error(error_message)

    def bind_context(self, **context: Any) -> "AuditLogger":
        """Create new audit logger dengan additional context."""
        new_context = {**self.base_context, **context}
        new_logger = AuditLogger()
        new_logger.base_context = new_context
        new_logger.logger = logger.bind(**new_context)
        return new_logger


def setup_audit_logging(repository: Any) -> None:
    """Setup loguru dengan audit system."""
    # Remove default handler untuk clean setup
    logger.remove()

    # Console logging untuk development
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG",
        format="{time} | {level} | {name} | {message}",
        colorize=False,
    )

    # Audit file logging (JSON Lines format)
    logger.add(
        "logs/audit_{time:YYYY-MM-DD}.jsonl",
        rotation="1 day",
        retention="90 days",
        serialize=True,
        level="INFO",
        filter=lambda record: record["extra"].get("audit", False),
    )

    # Database audit sink
    logger.add(
        AuditDatabaseSink(repository),
        level="INFO",
        filter=lambda record: record["extra"].get("audit", False),
    )

    # Console untuk development (optional)
    import sys

    logger.add(
        sys.stderr,
        level="ERROR",
        format="<red>{time}</red> | <level>{level}</level> | {message}",
        colorize=True,
    )


# Convenience functions untuk direct usage
def get_audit_logger(
    user_id: int | None = None, session_id: str | None = None
) -> AuditLogger:
    """Get configured audit logger."""
    return AuditLogger(user_id=user_id, session_id=session_id)


def log_system_start() -> None:
    """Log system startup."""
    logger.bind(
        audit=True,
        activity_type=ActivityType.SYSTEM_START,
        details={"startup_time": datetime.now().isoformat()},
    ).info("System started")
