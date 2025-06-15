"""Clean OOP authentication interface untuk solo developer use."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import streamlit as st

from src.config.logging.logging_config import log_activity  # Updated import
from src.models.session_manager import SessionManager
from src.models.user_manager import UserManager

# Configuration
USER_DATA_FILE = Path("user_info.json")
SESSION_DURATION_HOURS = 24

# Global instances - singleton pattern untuk Streamlit
_user_manager: UserManager | None = None
_session_manager: SessionManager | None = None


def _get_managers() -> tuple[UserManager, SessionManager]:
    """Get or create manager instances - singleton pattern."""
    global _user_manager, _session_manager

    if _user_manager is None:
        _user_manager = UserManager(USER_DATA_FILE, SESSION_DURATION_HOURS)

    if _session_manager is None:
        _session_manager = SessionManager(_user_manager)

    return _user_manager, _session_manager


def login(username: str, password: str) -> tuple[bool, str]:
    """Login user dengan clean OOP approach."""
    _, session_manager = _get_managers()
    success, message = session_manager.login(username, password)

    # Activity logging
    if success:
        log_activity(
            "LOGIN", f"User {username} logged in successfully", username=username
        )
    else:
        log_activity(
            "LOGIN_FAILED", f"Failed login attempt for {username}", username=username
        )

    return success, message


def logout() -> None:
    """Logout user dengan clean OOP approach."""
    username = st.session_state.get("username", "unknown")
    _, session_manager = _get_managers()
    session_manager.logout()

    # Activity logging
    log_activity("LOGOUT", f"User {username} logged out", username=username)


def is_authenticated() -> bool:
    """Check authentication status dengan clean OOP approach."""
    _, session_manager = _get_managers()
    return session_manager.is_authenticated()


def get_session_info() -> dict[str, Any]:
    """Get session information dengan clean OOP approach."""
    _, session_manager = _get_managers()
    return session_manager.get_session_info()


def change_password(old_password: str, new_password: str) -> tuple[bool, str]:
    """Change password dengan clean OOP approach."""
    user_manager, _ = _get_managers()
    return user_manager.change_password(old_password, new_password)


def require_auth(func: Callable[..., Any]) -> Callable[..., Any | None]:
    """Decorator to require authentication for functions."""

    def wrapper(*args: Any, **kwargs: Any) -> Any | None:
        if not is_authenticated():
            show_login_form()
            return None
        return func(*args, **kwargs)

    return wrapper


def show_login_form() -> None:
    """Display simple login form."""
    st.title("🔐 Login")

    # Show session restoration info
    if st.session_state.get("session_restored", False):
        st.success("✅ Session dipulihkan setelah refresh browser")
        del st.session_state.session_restored  # Clear flag

    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            success, message = login(username, password)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)


def show_user_info() -> None:
    """Display user info in sidebar."""
    if is_authenticated():
        username = st.session_state.get("username", "Unknown")
        st.sidebar.success(f"👤 {username}")

        # Show session info
        if st.session_state.get("session_restored", False):
            st.sidebar.info("🔄 Session restored")

        if st.sidebar.button("Logout"):
            logout()
            st.rerun()
