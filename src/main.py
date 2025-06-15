from datetime import datetime

import streamlit as st
from loguru import logger

from navigation import run_navigation
from src.authentication import is_authenticated, show_login_form, show_user_info
from src.config.logging import log_action, setup_logging


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

    # Audit page config setup
    log_action(
        action="app_page_config",
        message="Streamlit page configuration initialized",
        resource="app_main",
        detail={"page_title": "ETL Dashboard", "layout": "wide"},
    )


def setup_app_state() -> None:
    """Setup application state - guard pattern."""
    if "app_state_initialized" in st.session_state:
        return

    st.session_state.app_state_initialized = True
    st.session_state.app_start_time = datetime.now()
    st.session_state.app_initialized = True
    logger.info("=== ETL Dashboard Application Started ===")

    # Audit app state setup
    log_action(
        action="app_state_init",
        message="Application state initialized",
        resource="app_main",
        detail={"start_time": st.session_state.app_start_time.isoformat()},
    )


def main() -> None:
    """Main application entry point."""
    setup_page_config()

    # Setup logging with error handling
    log_status = setup_logging()
    if not log_status["success"]:
        st.error("⚠️ Logging setup incomplete - check console for details")

        # Audit logging setup issues
        log_action(
            action="logging_setup_error",
            message="Logging setup incomplete",
            resource="app_main",
            detail={"errors": log_status.get("errors", [])},
            level="ERROR",
        )

    setup_app_state()

    # Authentication check
    if not is_authenticated():
        # Audit authentication failure
        log_action(
            action="auth_required",
            message="User authentication required",
            resource="app_main",
            detail={"authenticated": False},
        )
        show_login_form()
        return

    # Audit successful authentication
    log_action(
        action="auth_success",
        message="User authentication successful",
        resource="app_main",
        detail={"authenticated": True},
    )

    # Show user info in sidebar
    show_user_info()

    # Run main navigation
    run_navigation()


if __name__ == "__main__":
    main()
