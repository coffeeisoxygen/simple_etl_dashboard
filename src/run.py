"""Simple ETL Dashboard - Main Application Entry Point."""

import sys
from pathlib import Path

# Add src to Python path for absolute imports
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from loguru import logger

from db.database import initialize_database
from log_setup import setup_smart_logging
from pages.auth.pg_auth import render_auth_page
from services.auth_manager import get_auth_manager  # ✅ NEW: Replace UserState import


def setup_app() -> bool:
    """Setup aplikasi: logging dan database initialization."""
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


def render_session_sidebar() -> None:
    """Render session information and timeout warnings in sidebar."""
    auth_manager = get_auth_manager()

    with st.sidebar:
        st.markdown("---")

        # Show current user info
        current_user = auth_manager.get_current_user()
        if current_user:
            st.markdown(f"**👤 Logged in as:** {current_user.name}")
            if current_user.is_admin:
                st.markdown("🔑 **Admin User**")

        # ✅ NEW: Session timeout warning with extend option
        timeout_warning = auth_manager.check_session_timeout_warning()
        if timeout_warning:
            st.warning(f"⏰ {timeout_warning}")

            # Allow user to extend session
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "🔄 Extend", use_container_width=True, help="Extend session"
                ):
                    if auth_manager.extend_session():
                        st.success("Session extended!")
                        st.rerun()
                    else:
                        st.error("Failed to extend")

            with col2:
                if st.button("🚪 Logout", use_container_width=True, help="Logout now"):
                    auth_manager.logout_with_cleanup()
                    st.rerun()


def logout():
    """Logout page function with AuthManager integration."""
    # ✅ CHANGED: Use AuthManager instead of UserState
    auth_manager = get_auth_manager()
    current_user = auth_manager.get_current_user()

    if not current_user:
        # User not authenticated, redirect to login
        st.switch_page("pages/auth/pg_auth.py")
        return

    st.title("🚪 Logout")

    # Show current user info
    col1, col2 = st.columns([1, 2])

    with col1:
        st.info("**Current Session:**")
        st.write(f"👤 **User:** {current_user.name}")
        st.write(f"🔑 **Role:** {'Admin' if current_user.is_admin else 'User'}")

        # ✅ NEW: Show session timeout info
        timeout_info = auth_manager.get_session_timeout_info()
        if timeout_info:
            st.write(
                f"⏰ **Session:** {timeout_info['time_remaining_minutes']} min left"
            )

    with col2:
        st.warning("⚠️ Anda akan keluar dari sistem")
        st.markdown("Klik tombol di bawah untuk logout:")

        # Logout button with proper cleanup
        if st.button("🚪 Confirm Logout", type="primary", use_container_width=True):
            # ✅ CHANGED: Use AuthManager for proper cleanup
            auth_manager.logout_with_cleanup()
            st.success("👋 Logout berhasil!")
            st.balloons()  # Fun animation
            st.rerun()


def main() -> None:
    """Main entry point following Streamlit docs pattern."""
    # Page configuration
    st.set_page_config(
        page_title="ETL Dashboard",
        page_icon="📊",
        layout="centered",
        initial_sidebar_state="auto",
    )

    # Infrastructure setup
    if not setup_app():
        st.error("❌ Application failed to initialize")
        st.stop()

    # ✅ CHANGED: Use AuthManager instead of UserState
    auth_manager = get_auth_manager()

    # ✅ FOLLOWING STREAMLIT DOCS PATTERN
    # Define pages
    login_page = st.Page(render_auth_page, title="Login", icon=":material/login:")
    logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

    # Dashboard
    dashboard = st.Page(
        "pages/dashboard/pg_dashboard.py",
        title="Dashboard",
        icon=":material/dashboard:",
        default=True,
    )
    analytics = st.Page(
        "pages/analytics/pg_analytics.py",
        title="Analytics",
        icon=":material/analytics:",
    )

    # Reports
    transaction = st.Page(
        "pages/reports/pg_transaksi.py",
        title="Transaction Report",
        icon=":material/receipt:",
    )
    sellin = st.Page(
        "pages/reports/pg_sellin.py",
        title="Sell-in Report",
        icon=":material/trending_up:",
    )
    visit = st.Page(
        "pages/reports/pg_visit.py",
        title="Visit Report",
        icon=":material/person_pin_circle:",
    )
    transfer = st.Page(
        "pages/reports/pg_transfer.py",
        title="Transfer Report",
        icon=":material/swap_horiz:",
    )
    rgu = st.Page(
        "pages/reports/pg_rgu.py", title="RGU Report", icon=":material/assessment:"
    )

    # Master Data
    site = st.Page(
        "pages/master/pg_site.py",
        title="Site Management",
        icon=":material/location_on:",
    )
    retailer = st.Page(
        "pages/master/pg_retailer.py",
        title="Retailer Management",
        icon=":material/store:",
    )
    territory = st.Page(
        "pages/master/pg_territory.py",
        title="Territory Management",
        icon=":material/map:",
    )
    allocation = st.Page(
        "pages/master/pg_allocation.py",
        title="Allocation Management",
        icon=":material/grid_view:",
    )
    business_info = st.Page(
        "pages/master/pg_bussines_info.py",
        title="Business Info",
        icon=":material/business:",
    )

    # Tools
    upload = st.Page(
        "pages/tools/pg_etls_tools.py", title="Data Upload", icon=":material/upload:"
    )

    # Info
    glossarium = st.Page(
        "pages/info/pg_glossarium.py", title="Glossarium", icon=":material/book:"
    )

    # Account
    profile = st.Page(
        "pages/account/pg_profile.py", title="Profile", icon=":material/person:"
    )

    # Admin (only for admin users)
    settings = st.Page(
        "pages/admin/pg_sys_settings.py", title="Settings", icon=":material/settings:"
    )

    # ✅ NAVIGATION SETUP - FOLLOWING DOCS PATTERN
    # ✅ CHANGED: Use AuthManager with auto-restore capability
    if auth_manager.is_authenticated():  # This automatically tries cookie restore!
        # ✅ NEW: Show session management in sidebar
        render_session_sidebar()

        # Get current user for permission checking
        current_user = auth_manager.get_current_user()

        # Build navigation based on user permissions
        nav_structure = {
            "Account": [logout_page],
            "Dashboard": [dashboard, analytics],
            "Reports": [transaction, sellin, visit, transfer, rgu],
            "Master Data": [site, retailer, territory, allocation, business_info],
            "Tools": [upload],
            "Info": [glossarium, profile],
        }

        # Add admin section if admin
        if current_user and current_user.is_admin:
            nav_structure["Admin"] = [settings]

        pg = st.navigation(nav_structure)
    else:
        # Only show login page
        pg = st.navigation([login_page])

    # Run the navigation
    pg.run()


if __name__ == "__main__":
    main()


# TODO: Add proper error handling for navigation failures
# PINNED: Consider adding breadcrumb navigation for better UX
# REMINDER: AuthManager handles auto-restore from cookies on app start
# NOTE: Session timeout warnings appear in sidebar when user is authenticated
