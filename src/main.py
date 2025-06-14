from datetime import datetime

import streamlit as st
from loguru import logger

from navigation import run_navigation
from src.config.log_setup import setup_logging


def setup_page_config() -> None:
    """Setup Streamlit page configuration."""
    if "page_config_initialized" in st.session_state:
        return

    st.set_page_config(
        page_title="ETL Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.session_state.page_config_initialized = True
    logger.info(f"=== Streamlit Page Config Initialized: {datetime.now()} ===")


def setup_app_state() -> None:
    """Setup application state - guard pattern."""
    if "app_state_initialized" in st.session_state:
        return

    st.session_state.app_state_initialized = True
    st.session_state.app_start_time = datetime.now()
    st.session_state.app_initialized = True
    logger.info("=== ETL Dashboard Application Started ===")


def main() -> None:
    """Main application entry point."""
    setup_page_config()  # Guard pattern
    setup_logging()  # Already has guard
    setup_app_state()  # Guard pattern

    run_navigation()


if __name__ == "__main__":
    main()
