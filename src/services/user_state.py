from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any

import streamlit as st

from schemas.auth.response import LoginResponse

# Internal keys yang di-manage oleh UserState service
SESSION_KEYS = {
    "is_authenticated": bool,
    "user_id": int,
    "username": str,
    "user_name": str,  # Display name
    "is_admin": bool,
    "is_active": bool,
    "login_timestamp": datetime,
}


class UserState:
    """Type-safe wrapper untuk Streamlit session state user management."""

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return st.session_state.get("is_authenticated", False)

    def get_user_id(self) -> int | None:
        """Get current user ID if authenticated."""
        return st.session_state.get("user_id") if self.is_authenticated() else None

    def get_username(self) -> str | None:
        """Get current username if authenticated."""
        return st.session_state.get("username") if self.is_authenticated() else None

    def get_user_name(self) -> str | None:
        """Get current user display name if authenticated."""
        return st.session_state.get("user_name") if self.is_authenticated() else None

    def is_admin(self) -> bool:
        """Check if current user has admin privileges."""
        return (
            st.session_state.get("is_admin", False)
            if self.is_authenticated()
            else False
        )

    def is_active(self) -> bool:
        """Check if current user account is active."""
        return (
            st.session_state.get("is_active", False)
            if self.is_authenticated()
            else False
        )

    def get_login_timestamp(self) -> datetime | None:
        """Get login timestamp if authenticated."""
        return (
            st.session_state.get("login_timestamp") if self.is_authenticated() else None
        )

    def login_user(self, user_data: LoginResponse) -> None:
        """Set user session data after successful login."""
        st.session_state["is_authenticated"] = True
        st.session_state["user_id"] = user_data.id
        st.session_state["username"] = user_data.username
        st.session_state["user_name"] = user_data.name
        st.session_state["is_admin"] = user_data.is_admin
        st.session_state["is_active"] = user_data.is_active
        st.session_state["login_timestamp"] = datetime.now()

    def logout_user(self) -> None:
        """Clear all user session data."""
        for key in SESSION_KEYS.keys():
            if key in st.session_state:
                del st.session_state[key]

    def logout(self) -> None:
        """Convenience method - alias for logout_user."""
        self.logout_user()

    def require_auth(self) -> None:
        """Guard function to ensure user is authenticated."""
        if not self.is_authenticated():
            st.error("🔒 Anda harus login terlebih dahulu")
            st.stop()

    def require_admin(self) -> None:
        """Guard function to ensure user has admin privileges."""
        self.require_auth()  # First check if authenticated
        if not self.is_admin():
            st.error("🚫 Akses ditolak: Hanya admin yang dapat mengakses halaman ini")
            st.stop()

    def require_active(self) -> None:
        """Guard function to ensure user account is active."""
        self.require_auth()  # First check if authenticated
        if not self.is_active():
            st.error("⚠️ Akun Anda tidak aktif. Hubungi administrator")
            st.stop()


# Convenience decorators for page-level protection
def require_auth(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require authentication for a function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        user_state = UserState()
        user_state.require_auth()
        return func(*args, **kwargs)

    return wrapper


def require_admin(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require admin privileges for a function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        user_state = UserState()
        user_state.require_admin()
        return func(*args, **kwargs)

    return wrapper


def require_active(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require active account for a function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        user_state = UserState()
        user_state.require_active()
        return func(*args, **kwargs)

    return wrapper
