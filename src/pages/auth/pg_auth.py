"""Authentication page with clean, focused authentication logic."""

import streamlit as st
from loguru import logger

from schemas.auth.request import LoginRequest
from services.auth_manager import get_auth_manager  # ✅ NEW IMPORT


@st.fragment
def render_login_form() -> None:
    """Render login form with validation and authentication."""
    st.subheader("🔐 Login")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input(
            "Password", type="password", placeholder="Enter your password"
        )
        submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password")
                return

            try:
                # ✅ CHANGED: Use AuthManager instead of direct auth_service
                auth_manager = get_auth_manager()
                login_request = LoginRequest(username=username, password=password)

                # This will handle login + cookie persistence automatically
                user_response = auth_manager.login_with_persistence(login_request)

                st.success(f"Welcome, {user_response.name}!")
                st.rerun()  # Refresh to show dashboard

            except ValueError as e:
                st.error(f"Login failed: {str(e)}")
                logger.warning(f"Login attempt failed for username: {username}")
            except Exception as e:
                st.error("An unexpected error occurred. Please try again.")
                logger.error(f"Unexpected login error: {e}")


def render_auth_page() -> None:
    """Main authentication page with login form."""
    # ✅ CHANGED: Use AuthManager for auth check
    auth_manager = get_auth_manager()

    # Check if already authenticated (with auto-restore from cookies)
    if auth_manager.is_authenticated():
        # User is logged in, redirect to dashboard
        st.switch_page("pages/dashboard/pg_dashboard.py")
        return

    # Show login form
    st.title("Simple ETL Dashboard")
    st.markdown("---")

    render_login_form()

    # Optional: Show debug info in development
    if st.checkbox("Show Debug Info", key="auth_debug"):
        st.json(auth_manager.get_session_info())


# TODO: Add forgot password functionality
# PINNED: Consider adding registration form for new users
# REMINDER: This page handles authentication only, dashboard logic is separate
