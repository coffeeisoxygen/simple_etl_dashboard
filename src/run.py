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
from services.user_state import UserState


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


def logout():
    """Logout page function."""
    user_state = UserState()

    st.title("🚪 Logout")

    # Show current user info
    col1, col2 = st.columns([1, 2])

    with col1:
        st.info("**Current Session:**")
        st.write(f"👤 **User:** {user_state.get_user_name()}")
        st.write(f"🔑 **Role:** {'Admin' if user_state.is_admin() else 'User'}")

        if login_time := user_state.get_login_timestamp():
            st.write(f"⏰ **Login:** {login_time.strftime('%H:%M:%S')}")

    with col2:
        st.warning("⚠️ Anda akan keluar dari sistem")
        st.markdown("Klik tombol di bawah untuk logout:")

        # Logout button
        if st.button("🚪 Confirm Logout", type="primary", use_container_width=True):
            user_state.logout_user()
            st.success("👋 Logout berhasil!")
            st.balloons()  # Fun animation
            st.rerun()


def main() -> None:
    """Main entry point following Streamlit docs pattern."""
    # Page configuration
    st.set_page_config(
        page_title="ETL Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Infrastructure setup
    if not setup_app():
        st.error("❌ Application failed to initialize")
        st.stop()

    # Initialize user state
    user_state = UserState()

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
    if user_state.is_authenticated():
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
        if user_state.is_admin():
            nav_structure["Admin"] = [settings]

        pg = st.navigation(nav_structure)
    else:
        # Only show login page
        pg = st.navigation([login_page])

    # Run the navigation
    pg.run()


if __name__ == "__main__":
    main()
