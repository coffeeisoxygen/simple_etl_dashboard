"""Session management dengan clean OOP approach."""

import uuid
from typing import Any

import streamlit as st
from loguru import logger
from src.models.user_manager import UserManager


class SessionContext:
    """Browser session context information."""

    def __init__(self, browser_session_id: str, app_session_id: str) -> None:
        self.browser_session_id = browser_session_id
        self.app_session_id = app_session_id

    @classmethod
    def generate_new(cls) -> "SessionContext":
        """Generate new session context."""
        return cls(
            browser_session_id=cls._get_browser_session_id(),
            app_session_id=str(uuid.uuid4()),
        )

    @staticmethod
    def _get_browser_session_id() -> str:
        """Get or create browser session ID."""
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx

            ctx = get_script_run_ctx()
            if ctx and hasattr(ctx, "session_id"):
                return ctx.session_id
        except Exception:
            pass

        # Fallback to session state
        if "browser_session_id" not in st.session_state:
            st.session_state.browser_session_id = str(uuid.uuid4())

        return st.session_state.browser_session_id


class SessionManager:
    """Manages authentication sessions dengan DI pattern."""

    def __init__(self, user_manager: UserManager) -> None:
        self.user_manager = user_manager

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Authenticate user dan create session."""
        if not self.user_manager.verify_password(username, password):
            logger.warning(f"Failed login attempt for user: {username}")
            return False, "Username atau password salah"

        # Generate session context
        session_ctx = SessionContext.generate_new()

        # Update persistent session
        self.user_manager.update_session(
            session_ctx.browser_session_id,
            session_ctx.app_session_id,
            active=True,
        )

        # Set Streamlit session state
        self._set_session_state(username, session_ctx)

        logger.info(f"User {username} logged in successfully")
        return True, "Login berhasil"

    def logout(self) -> None:
        """Clear session dan logout user."""
        self.user_manager.clear_session()
        self._clear_session_state()
        logger.info("User logged out")

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with auto-restore."""
        # Quick check from session state
        if st.session_state.get("authenticated", False):
            return True

        # Try to restore session from persistent data
        return self._restore_session()

    def _restore_session(self) -> bool:
        """Restore session from persistent data after refresh."""
        user_data = self.user_manager.load_user_data()

        if not user_data.session_active or user_data.is_session_expired():
            return False

        # Restore session state
        session_ctx = SessionContext(
            user_data.browser_session_id or "",
            user_data.app_session_id or "",
        )

        self._set_session_state(user_data.username, session_ctx)
        st.session_state.session_restored = True

        logger.info(f"Session restored for user: {user_data.username}")
        return True

    def _set_session_state(self, username: str, session_ctx: SessionContext) -> None:
        """Set Streamlit session state."""
        from datetime import datetime

        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.login_time = datetime.now()
        st.session_state.app_session_id = session_ctx.app_session_id
        st.session_state.browser_session_id = session_ctx.browser_session_id

    def _clear_session_state(self) -> None:
        """Clear Streamlit session state."""
        session_keys = [
            "authenticated",
            "username",
            "login_time",
            "app_session_id",
            "browser_session_id",
            "session_restored",
        ]

        for key in session_keys:
            if key in st.session_state:
                del st.session_state[key]

    def get_session_info(self) -> dict[str, Any]:
        """Get comprehensive session information."""
        user_data = self.user_manager.load_user_data()

        return {
            "authenticated": st.session_state.get("authenticated", False),
            "username": st.session_state.get("username", ""),
            "login_time": st.session_state.get("login_time", ""),
            "session_active": user_data.session_active,
            "session_expires": user_data.session_expires,
            "browser_session_id": st.session_state.get("browser_session_id", ""),
            "app_session_id": st.session_state.get("app_session_id", ""),
            "session_restored": st.session_state.get("session_restored", False),
        }
