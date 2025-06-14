"""Models package for ETL Dashboard application.

This package contains all data models and related utilities for the application:
- Commons: Base utilities, OperationResult, datetime handling
- Authentication: User models, login, password management
- Context: Browser context tracking for session security
- Session: Session management with dependency injection
- Audit: Activity logging with loguru integration
"""

# Commons exports
# Audit exports
from src.models.audit import (
    ActivityType,
    AuditDatabaseSink,
    AuditLog,
    AuditLogger,
    get_audit_logger,
    log_system_start,
    setup_audit_logging,
)

# Authentication exports
from src.models.authentication import (
    AdminSeedData,
    AuthenticationRules,
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordHash,
    User,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from src.models.commons import (
    DatabaseEntity,
    OperationResult,
    ValidationMixin,
    normalize_datetime,
)

# Context exports
from src.models.context import (
    BrowserContext,
    ContextProvider,
    MockContextProvider,
    StreamlitContextProvider,
)

# Session exports
from src.models.session import (
    Session,
    SessionManager,
    SessionState,
)

__all__ = [
    # Commons
    "DatabaseEntity",
    "OperationResult",
    "ValidationMixin",
    "normalize_datetime",
    # Authentication
    "User",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "LoginResponse",
    "PasswordChangeRequest",
    "PasswordHash",
    "AdminSeedData",
    "AuthenticationRules",
    # Context
    "BrowserContext",
    "ContextProvider",
    "StreamlitContextProvider",
    "MockContextProvider",
    # Session
    "Session",
    "SessionState",
    "SessionManager",
    # Audit
    "ActivityType",
    "AuditLog",
    "AuditLogger",
    "AuditDatabaseSink",
    "get_audit_logger",
    "log_system_start",
    "setup_audit_logging",
]
