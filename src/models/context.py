"""Browser context management untuk session tracking."""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class BrowserContext(BaseModel):
    """Model untuk browser context information."""

    session_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    timezone: str | None = None
    url: str | None = None
    locale: str | None = None

    def to_fingerprint(self) -> str:
        """Generate fingerprint string untuk comparison."""
        parts = [
            self.session_id or "unknown",
            self.ip_address or "unknown",
            (self.user_agent or "unknown")[:50],  # Truncate
            self.timezone or "UTC",
        ]
        return "|".join(parts)

    def is_similar_to(self, other: "BrowserContext", strict: bool = True) -> bool:
        """Compare dengan context lain."""
        if strict:
            return (
                self.session_id == other.session_id
                and self.ip_address == other.ip_address
                and self.user_agent == other.user_agent
            )
        else:
            return (
                self.session_id == other.session_id
                and self.ip_address == other.ip_address
            )

    model_config = {
        "str_strip_whitespace": True,
    }


class ContextProvider(ABC):
    """Abstract provider untuk browser context extraction."""

    @abstractmethod
    def get_current_context(self) -> BrowserContext:
        """Extract current browser context."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check apakah context provider available."""
        pass


class StreamlitContextProvider(ContextProvider):
    """Streamlit-specific context provider (extracted dari context_info.py)."""

    def get_current_context(self) -> BrowserContext:
        """Extract context dari Streamlit runtime."""
        try:
            import streamlit as st
            from streamlit.runtime.scriptrunner import get_script_run_ctx

            ctx = get_script_run_ctx()

            return BrowserContext(
                session_id=ctx.session_id if ctx else None,
                ip_address=getattr(st.context, "ip_address", None),
                user_agent=getattr(st.context, "headers", {}).get("user-agent"),
                timezone=getattr(st.context, "timezone", None),
                url=getattr(st.context, "url", None),
                locale=getattr(st.context, "locale", None),
            )
        except Exception:
            return self._get_fallback_context()

    def is_available(self) -> bool:
        """Check apakah Streamlit context available."""
        try:
            import streamlit as st

            return hasattr(st, "context")
        except ImportError:
            return False

    def _get_fallback_context(self) -> BrowserContext:
        """Fallback context untuk development."""
        return BrowserContext(
            session_id="dev-session",
            ip_address="127.0.0.1",
            user_agent="development",
            timezone="UTC",
            url="http://localhost:8501",
        )


class MockContextProvider(ContextProvider):
    """Mock context provider untuk testing."""

    def __init__(self, mock_context: BrowserContext) -> None:
        self.mock_context = mock_context

    def get_current_context(self) -> BrowserContext:
        """Return mock context."""
        return self.mock_context

    def is_available(self) -> bool:
        """Always available untuk testing."""
        return True
