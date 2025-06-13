import sys
from datetime import datetime

import streamlit as st
from loguru import logger

from navigation import run_navigation


def setup_logging() -> None:
    """Setup Loguru logging configuration."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
    )
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",
        rotation="10 MB",
    )
    logger.info("Logging configured")


def setup_page_config() -> None:
    """Setup Streamlit page configuration."""
    st.set_page_config(
        page_title="ETL Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    logger.info("Page configuration set")


def main() -> None:
    """Main application entry point."""
    # Setup page configuration first
    setup_page_config()

    # Setup logging
    setup_logging()
    logger.info("=== ETL Dashboard Application Started ===")

    # Initialize session state if needed
    if "app_initialized" not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.app_start_time = datetime.now()
        logger.info("Session state initialized")

    # Run the navigation system
    logger.info("Launching navigation system")
    run_navigation()


if __name__ == "__main__":
    main()
