"""Main application entry point - Clean & Simple.

Philosophy: KISS principle, minimal error handling, focus on core flow.
"""

import time

import streamlit as st
from loguru import logger

from src.core.state_management import (
    get_system_info,
    get_user_state,
    initialize_app,
    is_app_ready,
)
from src.dashboard.navigation import run_navigation


def setup_page_config() -> None:
    """Setup Streamlit page configuration - MUST be called first."""
    st.set_page_config(
        page_title="ETL Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def show_login_form() -> None:
    """Display simple login form."""
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="admin")
        submit = st.form_submit_button("Login")

        if submit:
            if username == "admin" and password == "admin":
                user_state = get_user_state()
                user_state.login(user_id="admin", username=username)
                st.success("✅ Login berhasil!")
                st.rerun()
            else:
                st.error("❌ Username atau password salah")


def show_user_info() -> None:
    """Display user info in sidebar."""
    user_state = get_user_state()

    if user_state.is_authenticated():
        username = user_state.get_username() or "Unknown"
        st.sidebar.success(f"👤 {username}")

        if st.sidebar.button("Logout"):
            user_state.logout()
            st.rerun()


def show_debug_toggle() -> None:
    """Simple debug toggle for development."""
    if st.sidebar.checkbox("🔧 Debug Mode", key="show_debug_panel"):
        try:
            system_info = get_system_info()
            with st.sidebar.expander("Debug Info"):
                st.json(system_info)
        except Exception as e:
            st.sidebar.error(f"Debug error: {e}")


def main() -> None:
    """Main application entry point - simplified."""
    # Setup page config first
    setup_page_config()

    # Initialize app
    if not initialize_app():
        st.error("❌ Failed to initialize app")
        if st.button("🔄 Retry"):
            st.rerun()
        return

    # Wait for app ready
    if not is_app_ready():
        st.info("🔄 Loading...")
        time.sleep(1)
        st.rerun()
        return

    # Get user state
    user_state = get_user_state()

    # Show debug toggle in development
    show_debug_toggle()

    # Authentication flow
    if not user_state.is_authenticated():
        show_login_form()
        return

    # Show user info
    show_user_info()

    # Run navigation
    try:
        run_navigation()
    except Exception as e:
        logger.error(f"Navigation error: {e}")
        st.error("❌ Navigation error occurred")

        if st.button("🔄 Refresh"):
            st.rerun()


if __name__ == "__main__":
    main()

# TODO: Add basic health monitoring
# PINNED: Consider adding simple crash recovery
