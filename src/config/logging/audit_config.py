"""Audit logging configuration for business operations tracking."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import streamlit as st
from loguru import logger

if TYPE_CHECKING:
    from loguru import Logger, Message, Record


class AuditLogger:
    """Audit logger for business operations tracking."""

    def __init__(self, db_path: str = "logs/audit.sqlite") -> None:
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        self._setup_database()
        self._setup_logger()

    def _setup_database(self) -> None:
        """Setup audit database and table."""
        # Ensure logs directory exists
        self.db_path.parent.mkdir(exist_ok=True)

        conn = self._get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                user_id TEXT,
                session_id TEXT,
                action TEXT NOT NULL,
                resource TEXT,
                message TEXT NOT NULL,
                detail TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Constraints
                CHECK (length(action) > 0),
                CHECK (length(message) > 0)
            )
        """)

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_session ON audit_log(session_id)",
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

        conn.commit()
        logger.debug(f"Audit database initialized: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False, timeout=30.0
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _setup_logger(self) -> None:
        """Setup loguru sink for audit logging."""
        logger.add(
            self._sqlite_sink,
            level="INFO",
            filter=self._audit_filter,
            enqueue=True,
            catch=True,
        )

    def _audit_filter(self, record: "Record") -> bool:
        """Filter for audit log entries."""
        return "audit_action" in record["extra"]

    def _sqlite_sink(self, message: "Message") -> None:
        """Loguru sink for SQLite audit logging."""
        try:
            record = message.record
            extras = record["extra"]

            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO audit_log (
                    timestamp, level, user_id, session_id, action,
                    resource, message, detail, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now(),
                    record["level"].name,
                    extras.get("user_id"),
                    extras.get("session_id"),
                    extras.get("audit_action"),
                    extras.get("resource"),
                    record["message"],
                    str(extras.get("detail", {})),
                    extras.get("ip_address"),
                    extras.get("user_agent"),
                ),
            )
            conn.commit()

        except Exception as e:
            # Log to development logger, don't fail the operation
            logger.error(f"Audit logging failed: {e}")

    def get_context_logger(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> "Logger":
        """Get audit logger with context."""
        # Auto-populate from Streamlit context if available
        if user_id is None and hasattr(st, "session_state"):
            user_id = getattr(st.session_state, "user_id", None)

        if session_id is None and hasattr(st, "session_state"):
            session_id = getattr(st.session_state, "session_id", None)

        # Get request context for web info
        if hasattr(st, "context") and st.context:
            try:
                headers = st.context.headers
                if ip_address is None:
                    ip_address = headers.get("x-forwarded-for", "unknown")
                if user_agent is None:
                    user_agent = headers.get("user-agent", "unknown")
            except Exception:
                pass  # Context might not be available in all scenarios

        return logger.bind(
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address or "unknown",
            user_agent=user_agent or "unknown",
        )

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


# Global audit logger instance
_audit_logger: AuditLogger | None = None


def get_audit_logger() -> AuditLogger:
    """Get or create audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_action(
    action: str,
    message: str,
    resource: str | None = None,
    detail: dict | None = None,
    user_id: str | None = None,
    level: str = "INFO",
) -> None:
    """Helper function for quick audit logging."""
    audit_logger = get_audit_logger()
    context_logger = audit_logger.get_context_logger(user_id=user_id)

    log_method = getattr(context_logger, level.lower(), context_logger.info)
    log_method(message, audit_action=action, resource=resource, detail=detail or {})


def get_audit_context(user_id: str | None = None) -> "Logger":
    """Get audit logger with context for multiple operations."""
    audit_logger = get_audit_logger()
    return audit_logger.get_context_logger(user_id=user_id)
