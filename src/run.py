"""Simple ETL Dashboard - Main Application Entry Point.

KISS principle: Keep it simple for MVP.
Added tracking untuk monitor Streamlit re-run behavior dan database initialization.
"""

import sys
from datetime import datetime
from pathlib import Path

# FIXED: Add src to Python path for absolute imports
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from loguru import logger
from sqlalchemy import select

from db.database import get_database_status, get_session, get_sql_manager
from models.base import Base
from models.user_model import User
from shared.log_setup import setup_smart_logging
from utils.hashing import hash_password


def track_app_run() -> None:
    """Track app runs untuk monitoring re-run behavior."""
    # Initialize tracking counters
    if "app_run_count" not in st.session_state:
        st.session_state.app_run_count = 0
    if "first_run_time" not in st.session_state:
        st.session_state.first_run_time = datetime.now()
    if "last_run_time" not in st.session_state:
        st.session_state.last_run_time = datetime.now()

    # Update counters
    st.session_state.app_run_count += 1
    st.session_state.last_run_time = datetime.now()

    logger.debug(f"App run #{st.session_state.app_run_count}")


def setup_app() -> bool:
    """Simple app setup - no over-engineering."""
    # Track database setup attempts
    if "db_setup_attempts" not in st.session_state:
        st.session_state.db_setup_attempts = 0

    # 1. Setup logging (once per session)
    if "logging_setup" not in st.session_state:
        try:
            setup_smart_logging()
            st.session_state.logging_setup = True
            st.session_state.logging_setup_time = datetime.now()
            logger.info("✅ Logging configured")
        except Exception as e:
            st.error(f"Logging setup failed: {e}")
            return False

    # 2. Setup database (once per session)
    if "db_setup" not in st.session_state:
        st.session_state.db_setup_attempts += 1
        logger.info(f"Database setup attempt #{st.session_state.db_setup_attempts}")

        try:
            # No need manual directory creation - SQL manager handles it
            sql_manager = get_sql_manager()

            # Create tables
            Base.metadata.create_all(bind=sql_manager.get_engine())

            # Create admin user if doesn't exist
            with get_session() as session:
                admin = session.execute(
                    select(User).where(User.username == "admin")
                ).scalar_one_or_none()

                if not admin:
                    admin = User(
                        username="admin",
                        name="Super Admin",
                        password_hash=hash_password("admin123"),
                        is_admin=True,
                        is_active=True,
                    )
                    session.add(admin)
                    session.commit()
                    logger.info("✅ Admin user created: admin/admin123")
                else:
                    logger.info("Admin user already exists")

            st.session_state.db_setup = True
            st.session_state.db_setup_time = datetime.now()
            logger.info("✅ Database configured")

        except Exception as e:
            st.error(f"Database setup failed: {e}")
            logger.error(f"Database error: {e}")
            return False

    return True


def render_tracking_dashboard() -> None:
    """Render tracking dashboard untuk monitor app behavior."""
    st.sidebar.header("🔍 App Tracking")

    # Run statistics
    st.sidebar.subheader("📊 Run Statistics")
    st.sidebar.metric("Total Runs", st.session_state.get("app_run_count", 0))

    if "first_run_time" in st.session_state:
        uptime = datetime.now() - st.session_state.first_run_time
        st.sidebar.metric("Uptime", f"{uptime.total_seconds():.1f}s")

    if "last_run_time" in st.session_state:
        st.sidebar.text(
            f"Last Run: {st.session_state.last_run_time.strftime('%H:%M:%S')}"
        )

    # Database statistics
    st.sidebar.subheader("🗄️ Database Stats")
    st.sidebar.metric("DB Setup Attempts", st.session_state.get("db_setup_attempts", 0))

    db_status = "✅ Ready" if st.session_state.get("db_setup") else "❌ Not Ready"
    st.sidebar.text(f"Status: {db_status}")

    if "db_setup_time" in st.session_state:
        st.sidebar.text(
            f"Setup At: {st.session_state.db_setup_time.strftime('%H:%M:%S')}"
        )

    # Interactive buttons untuk testing
    st.sidebar.subheader("🧪 Test Buttons")

    if st.sidebar.button("🔄 Force Re-run"):
        st.rerun()

    if st.sidebar.button("🗑️ Clear Session"):
        # Clear all session state except tracking
        keys_to_keep = ["app_run_count", "first_run_time"]
        keys_to_clear = [k for k in st.session_state.keys() if k not in keys_to_keep]
        for key in keys_to_clear:
            del st.session_state[key]
        st.rerun()

    if st.sidebar.button("💾 Database Health Check"):
        with st.sidebar:
            with st.spinner("Checking database..."):
                health = get_database_status()
                if health.get("status") == "healthy":
                    st.success("Database is healthy!")
                else:
                    st.error("Database has issues!")
                st.json(health)


def render_main_content() -> None:
    """Render main application content."""
    st.title("🚀 Simple ETL Dashboard")

    # Status indicators
    col1, col2, col3 = st.columns(3)

    with col1:
        logging_status = "✅" if st.session_state.get("logging_setup") else "❌"
        st.metric("Logging", logging_status)

    with col2:
        db_status = "✅" if st.session_state.get("db_setup") else "❌"
        st.metric("Database", db_status)

    with col3:
        run_count = st.session_state.get("app_run_count", 0)
        st.metric("App Runs", run_count)

    # Main content area
    st.header("📋 App Status")
    st.success("✅ App initialized successfully!")
    st.info("👈 Check the sidebar for tracking information and test buttons")

    # Simple interaction test
    st.header("🧪 Interaction Test")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📝 Add Counter", key="add_counter"):
            if "user_counter" not in st.session_state:
                st.session_state.user_counter = 0
            st.session_state.user_counter += 1
            st.success(f"Counter: {st.session_state.user_counter}")

    with col2:
        if st.button("🔄 Reset Counter", key="reset_counter"):
            st.session_state.user_counter = 0
            st.info("Counter reset to 0")

    # Display current counter
    if "user_counter" in st.session_state:
        st.write(f"**Current Counter Value:** {st.session_state.user_counter}")


def render_debug_info() -> None:
    """Render detailed debug information."""
    if st.expander("🐛 Debug Information", expanded=False):
        st.subheader("Session State")
        debug_info = {
            "session_keys": list(st.session_state.keys()),
            "session_state": dict(st.session_state),
        }
        st.json(debug_info)

        st.subheader("Database Status")
        try:
            db_status = get_database_status()
            st.json(db_status)
        except Exception as e:
            st.error(f"Failed to get database status: {e}")

        st.subheader("System Info")
        system_info = {
            "current_time": datetime.now().isoformat(),
            "streamlit_version": st.__version__,
            "python_version": sys.version,
        }
        st.json(system_info)


def main() -> None:
    """Main application entry point dengan tracking."""
    st.set_page_config(
        page_title="ETL Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Track app runs first
    track_app_run()

    # Setup app
    if not setup_app():
        st.error("❌ App initialization failed")
        st.stop()

    # Render UI components
    render_tracking_dashboard()
    render_main_content()
    render_debug_info()


if __name__ == "__main__":
    main()
