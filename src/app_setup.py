"""Application setup and initialization utilities."""

import streamlit as st
from loguru import logger

from db.database import initialize_database
from log_setup import setup_smart_logging


@st.cache_resource
def setup_app() -> bool:
    """Setup application: logging and database initialization."""
    # Setup logging (once per session)
    if "logging_setup" not in st.session_state:
        try:
            setup_smart_logging()
            st.session_state.logging_setup = True
            logger.info("✅ Logging configured")
        except Exception as e:
            st.error(f"❌ Logging setup failed: {e}")
            return False

    # Setup database (once per session)
    if "db_setup" not in st.session_state:
        try:
            logger.info("🔄 Initializing database...")
            if initialize_database():
                st.session_state.db_setup = True
                logger.info("✅ Database initialized")
            else:
                st.error("❌ Database initialization failed")
                return False
        except Exception as e:
            st.error(f"❌ Database setup failed: {e}")
            logger.error(f"Database error: {e}")
            return False

    return True


def configure_page() -> None:
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="ETL Dashboard",
        page_icon="📊",
        layout="centered",
        initial_sidebar_state="auto",
    )
