"""Session management models dengan dependency injection untuk context."""

from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.models.commons import DatabaseEntity, OperationResult, ValidationMixin
from src.models.context import ContextProvider


class SessionState(BaseModel):
    """Simple session state untuk Streamlit data persistence."""

    data: dict[str, Any] = Field(default_factory=dict, description="Session data")

    def set(self, key: str, value: Any) -> None:
        """Set session data."""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get session data."""
        return self.data.get(key, default)

    def remove(self, key: str) -> None:
        """Remove session data."""
        self.data.pop(key, None)

    def clear(self) -> None:
        """Clear semua session data."""
        self.data.clear()

    model_config = {
        "arbitrary_types_allowed": True,
    }


class Session(DatabaseEntity):
    """Simple session model dengan context injection."""

    user_id: int = Field(..., description="User ID")
    session_token: str = Field(..., min_length=1, description="Session token")
    browser_fingerprint: str = Field(..., description="Browser fingerprint string")
    session_state: SessionState = Field(
        default_factory=SessionState, description="Session data"
    )
    expires_at: datetime = Field(..., description="Expiry time")
    is_active: bool = Field(default=True, description="Active status")
    last_activity: datetime = Field(
        default_factory=datetime.utcnow, description="Last activity"
    )

    @field_validator("session_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Validate session token."""
        return ValidationMixin.validate_not_empty(v, "Session token")

    def is_expired(self) -> bool:
        """Check expired status."""
        return datetime.utcnow() >= self.expires_at

    def is_valid(self) -> bool:
        """Check session validity."""
        return self.is_active and not self.is_expired()

    def update_activity(self) -> None:
        """Update last activity."""
        self.last_activity = datetime.utcnow()
        # No mark_updated() needed - act_date handles record timestamp


class SessionManager:
    """Session manager dengan context provider injection."""

    def __init__(self, context_provider: ContextProvider) -> None:
        self.context_provider = context_provider

    def create_session_token(self) -> str:
        """Generate secure session token."""
        import secrets

        return secrets.token_urlsafe(32)

    def create_session(self, user_id: int, hours: int = 24) -> Session:
        """Create session dengan current context."""
        current_context = self.context_provider.get_current_context()

        return Session(
            user_id=user_id,
            session_token=self.create_session_token(),
            browser_fingerprint=current_context.to_fingerprint(),
            expires_at=datetime.now() + timedelta(hours=hours),
            act_date=datetime.now(UTC),  # Session creation time
        )

    def validate_session_context(
        self, session: Session, strict: bool = True
    ) -> OperationResult[bool]:
        """Validate session dengan current context."""
        if not session.is_valid():
            return OperationResult.error_result(
                message="Session tidak valid atau expired", error_code="INVALID_SESSION"
            )

        current_context = self.context_provider.get_current_context()
        current_fingerprint = current_context.to_fingerprint()

        if strict and session.browser_fingerprint != current_fingerprint:
            return OperationResult.error_result(
                message="Browser context berubah", error_code="CONTEXT_CHANGED"
            )

        return OperationResult.success_result(
            data=True, message="Session context valid"
        )
