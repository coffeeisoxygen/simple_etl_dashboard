"""Main application entry point untuk ETL Dashboard dengan database & logging integration."""

from datetime import datetime
from typing import Any

import streamlit as st
from loguru import logger

from src.authentication import is_authenticated, show_login_form, show_user_info
from src.config.logging.logging_config import log_activity, setup_logging
from src.database import get_database_manager
from src.navigation import run_navigation


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

    # Activity logging - updated
    log_activity(
        "APP_CONFIG",
        "Streamlit page configuration initialized",
        page_title="ETL Dashboard",
        layout="wide",
    )


def setup_logging_system() -> dict[str, Any]:
    """Setup logging system dengan comprehensive error handling."""
    try:
        success = setup_logging()

        if success:
            logger.info("=== Logging System Initialized Successfully ===")
            log_activity("LOG_INIT", "Logging system initialized successfully")
            return {"success": True, "errors": []}
        else:
            logger.error("Logging system initialization failed")
            return {"success": False, "errors": ["Logging setup failed"]}

    except Exception as e:
        logger.error(f"Critical logging setup error: {e}")
        return {"success": False, "errors": [str(e)]}


def setup_database_system() -> dict[str, Any]:
    """Setup database system dengan graceful fallback."""
    try:
        # Initialize database manager
        db_manager = get_database_manager()

        # Get database info untuk health check
        db_info = db_manager.get_database_info()

        if "error" in db_info:
            logger.error(f"Database system error: {db_info['error']}")
            log_activity(
                "DB_INIT_ERROR",
                f"Database initialization failed: {db_info['error']}",
                error=db_info["error"],
            )
            return {
                "success": False,
                "manager": None,
                "error": db_info["error"],
                "fallback": True,
            }

        # Store database manager di session state
        st.session_state.db_manager = db_manager
        st.session_state.db_info = db_info

        logger.info("=== Database System Initialized Successfully ===")
        log_activity(
            "DB_INIT",
            "Database system initialized successfully",
            master_db_exists=db_info["master_database"]["file_exists"],
            monthly_databases=len(db_info["monthly_databases"]),
        )

        return {"success": True, "manager": db_manager, "info": db_info}

    except Exception as e:
        logger.error(f"Database system initialization failed: {e}")
        log_activity(
            "DB_INIT_CRITICAL", f"Critical database error: {str(e)}", error=str(e)
        )

        return {"success": False, "manager": None, "error": str(e), "fallback": True}


def setup_app_state() -> None:
    """Setup application state dengan database integration."""
    if "app_state_initialized" in st.session_state:
        return

    st.session_state.app_state_initialized = True
    st.session_state.app_start_time = datetime.now()
    st.session_state.app_initialized = True

    logger.info("=== ETL Dashboard Application Started ===")

    # Activity logging - updated
    log_activity(
        "APP_START",
        "ETL Dashboard application started",
        app_start_time=st.session_state.app_start_time.isoformat(),
        session_id=st.session_state.get("session_id", "unknown"),
    )


def show_system_status() -> None:
    """Show system status untuk debugging dan monitoring."""
    if not st.session_state.get("show_system_status", False):
        return

    with st.sidebar.expander("🔧 System Status", expanded=False):
        # Logging status
        st.write("**Logging System:**")
        st.success(
            "✅ Active"
        ) if "logging_initialized" in st.session_state else st.error("❌ Failed")

        # Database status
        st.write("**Database System:**")
        if hasattr(st.session_state, "db_manager") and st.session_state.db_manager:
            st.success("✅ Connected")
            if hasattr(st.session_state, "db_info"):
                db_info = st.session_state.db_info
                st.caption(
                    f"Master DB: {'✅' if db_info['master_database']['file_exists'] else '❌'}"
                )
                st.caption(f"Monthly DBs: {len(db_info['monthly_databases'])}")
        else:
            st.warning("⚠️ Fallback Mode")

        # App uptime
        if "app_start_time" in st.session_state:
            uptime = datetime.now() - st.session_state.app_start_time
            st.caption(f"Uptime: {uptime}")


def handle_startup_errors(
    log_status: dict[str, Any], db_status: dict[str, Any]
) -> None:
    """Handle startup errors dengan user-friendly messaging."""
    has_errors = False

    # Logging errors
    if not log_status["success"]:
        st.error("⚠️ Logging system issues detected - check console for details")
        has_errors = True

        log_activity(
            "STARTUP_ERROR",
            "Logging system startup error",
            errors=log_status.get("errors", []),
        )

    # Database errors (non-critical)
    if not db_status["success"] and not db_status.get("fallback", False):
        st.error("❌ Database system failed to initialize")
        has_errors = True

    elif not db_status["success"] and db_status.get("fallback", False):
        st.info("ℹ️ Running in development mode - some features may be limited")

    # Show system status toggle untuk debugging
    if has_errors:
        if st.sidebar.button("🔧 Show System Status"):
            st.session_state.show_system_status = True
            st.rerun()


def main() -> None:
    """Main application entry point dengan comprehensive system integration."""
    # Setup page config first
    setup_page_config()

    # Initialize logging system
    log_status = setup_logging_system()

    # Initialize database system
    db_status = setup_database_system()

    # Setup application state
    setup_app_state()

    # Handle any startup errors
    handle_startup_errors(log_status, db_status)

    # Show system status jika diminta
    show_system_status()

    # Authentication check
    if not is_authenticated():
        log_activity(
            "AUTH_REQUIRED", "User authentication required", authenticated=False
        )
        show_login_form()
        return

    # Log successful authentication
    username = st.session_state.get("username", "unknown")
    log_activity(
        "AUTH_SUCCESS",
        f"User {username} authenticated successfully",
        username=username,
        authenticated=True,
    )

    # Show user info dalam sidebar
    show_user_info()

    # Run main navigation system
    try:
        run_navigation()
    except Exception as e:
        logger.error(f"Navigation system failed: {e}")
        log_activity(
            "NAV_CRITICAL",
            f"Navigation system critical failure: {str(e)}",
            error=str(e),
        )

        st.error("❌ Navigation system encountered a critical error")
        st.exception(e)

        # Provide fallback navigation
        if st.button("🔄 Restart Application"):
            # Clear relevant session state
            keys_to_clear = ["nav_manager", "navigation_manager_initialized"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()
