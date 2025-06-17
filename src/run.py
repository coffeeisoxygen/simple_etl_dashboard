"""Simple ETL Dashboard - Main Application Entry Point.

Clean entry point dengan proper authentication routing dan minimal setup.
Uses established service patterns untuk database dan user management.
"""

import sys
from pathlib import Path

# Add src to Python path for absolute imports
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from loguru import logger

from db.database import get_database_status, initialize_database
from log_setup import setup_smart_logging  # ← FIXED import path
from pages.auth.pg_auth import render_auth_page
from services.user_state import UserState


def setup_app() -> bool:
    """Setup aplikasi: logging dan database initialization.

    Returns:
        True jika setup berhasil, False jika gagal
    """
    # Setup logging (once per session)
    if "logging_setup" not in st.session_state:
        try:
            setup_smart_logging()
            st.session_state.logging_setup = True
            logger.info("✅ Logging configured")
        except Exception as e:
            st.error(f"Logging setup failed: {e}")
            return False

    # Setup database (once per session)
    if "db_setup" not in st.session_state:
        try:
            logger.info("Initializing database...")

            if initialize_database():
                st.session_state.db_setup = True
                logger.info("✅ Database initialized")
            else:
                st.error("❌ Database initialization failed")
                return False

        except Exception as e:
            st.error(f"Database setup failed: {e}")
            logger.error(f"Database error: {e}")
            return False

    return True


def render_authenticated_app() -> None:
    """Render main application untuk authenticated users."""
    user_state = UserState()

    st.title("🚀 ETL Dashboard")

    # Welcome message
    st.success(f"Selamat datang, {user_state.get_user_name()}!")

    # Basic navigation tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📁 ETL Tools", "⚙️ Settings"])

    with tab1:
        st.header("📊 Dashboard")
        st.info("Main dashboard akan diimplementasikan di sini")

        # Quick stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Status", "Ready")
        with col2:
            st.metric("Role", "Admin" if user_state.is_admin() else "User")

    with tab2:
        st.header("📁 ETL Tools")
        st.info("CSV upload dan processing tools akan diimplementasikan di sini")

        # Placeholder untuk ETL features
        st.write("**Fitur yang akan datang:**")
        st.write("- CSV File Upload")
        st.write("- Data Validation")
        st.write("- Data Transformation")
        st.write("- Database Storage")
        st.write("- Data Visualization")

    with tab3:
        st.header("⚙️ Settings")

        # User settings
        st.subheader("👤 User Settings")
        with st.expander("User Information"):
            st.write(f"**Username:** {user_state.get_username()}")
            st.write(f"**Name:** {user_state.get_user_name()}")
            st.write(f"**Role:** {'Admin' if user_state.is_admin() else 'User'}")

        # Admin tools
        if user_state.is_admin():
            st.subheader("🔧 Admin Tools")
            if st.button("📊 Database Health Check"):
                with st.spinner("Checking database health..."):
                    health = get_database_status()
                    if health.get("status") == "healthy":
                        st.success("✅ Database is healthy!")
                    else:
                        st.error("❌ Database has issues!")

                    with st.expander("Detailed Health Info"):
                        st.json(health)


def main() -> None:
    """Main application entry point dengan authentication routing."""
    # App configuration - MUST BE FIRST STREAMLIT COMMAND
    st.set_page_config(
        page_title="ETL Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Setup app infrastructure
    if not setup_app():
        st.error("❌ App initialization failed")
        st.stop()

    # Authentication routing
    user_state = UserState()

    if not user_state.is_authenticated():
        # Show authentication page
        render_auth_page()
    else:
        # Show main application
        render_authenticated_app()

        # Logout option in sidebar
        with st.sidebar:
            st.markdown("---")
            if st.button("🚪 Logout", key="sidebar_logout"):
                user_state.logout_user()
                st.rerun()


if __name__ == "__main__":
    main()
