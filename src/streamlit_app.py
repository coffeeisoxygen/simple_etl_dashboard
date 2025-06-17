"""Simple ETL Dashboard - Streamlit Official Pattern Entry Point."""

import streamlit as st
from config.app_setup import configure_page, setup_app

from schemas.auth.request import LoginRequest
from services.auth_manager import get_auth_manager


def login():
    """Simple login function following Streamlit pattern."""
    st.title("🔐 ETL Dashboard")
    st.markdown("Sign in to continue")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input(
            "Password", type="password", placeholder="Enter password"
        )
        submitted = st.form_submit_button(
            "Sign In", use_container_width=True, type="primary"
        )

        if submitted:
            if not username or not password:
                st.error("Please enter both username and password")
                return

            try:
                # ✅ Use existing auth architecture for business logic
                auth_manager = get_auth_manager()
                login_request = LoginRequest(username=username, password=password)
                user_response = auth_manager.login_with_persistence(login_request)

                st.success(f"Welcome, {user_response.name}!")
                st.rerun()

            except ValueError as e:
                st.error(f"Login failed: {str(e)}")

    # Login help
    with st.expander("💡 Default Credentials"):
        st.info("Username: **admin** | Password: **admin123**")


def logout():
    """Simple logout function following Streamlit pattern."""
    auth_manager = get_auth_manager()
    current_user = auth_manager.get_current_user()

    if current_user:
        st.write(f"👋 **{current_user.name}**")
        st.write("Are you sure you want to sign out?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes, Sign Out", type="primary", use_container_width=True):
                # ✅ Use existing auth cleanup
                auth_manager.logout_with_cleanup()
                st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.rerun()


def main():
    """Main entry point following Streamlit official pattern."""
    # ✅ 1. Infrastructure setup (once)
    configure_page()
    if not setup_app():
        st.error("❌ Application failed to initialize")
        st.stop()

    # ✅ 2. Check cookies & restore session (automatic)
    auth_manager = get_auth_manager()

    # ✅ 3. Check user authentication (with auto-restore)
    is_authenticated = auth_manager.is_authenticated()

    # ✅ 4. Create page objects
    login_page = st.Page(login, title="🔐 Sign In", icon=":material/login:")
    logout_page = st.Page(logout, title="🚪 Sign Out", icon=":material/logout:")

    # App pages (only created when authenticated)
    if is_authenticated:
        current_user = auth_manager.get_current_user()
        is_admin = current_user.is_admin if current_user else False

        # Dashboard pages
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

        # Report pages
        transaction = st.Page(
            "pages/reports/pg_transaksi.py",
            title="Transaction",
            icon=":material/receipt:",
        )
        sellin = st.Page(
            "pages/reports/pg_sellin.py", title="Sell-in", icon=":material/trending_up:"
        )
        visit = st.Page(
            "pages/reports/pg_visit.py",
            title="Visit",
            icon=":material/person_pin_circle:",
        )
        transfer = st.Page(
            "pages/reports/pg_transfer.py",
            title="Transfer",
            icon=":material/swap_horiz:",
        )
        rgu = st.Page(
            "pages/reports/pg_rgu.py", title="RGU", icon=":material/assessment:"
        )

        # Master data pages
        site = st.Page(
            "pages/master/pg_site.py", title="Site", icon=":material/location_on:"
        )
        retailer = st.Page(
            "pages/master/pg_retailer.py", title="Retailer", icon=":material/store:"
        )
        territory = st.Page(
            "pages/master/pg_territory.py", title="Territory", icon=":material/map:"
        )
        allocation = st.Page(
            "pages/master/pg_allocation.py",
            title="Allocation",
            icon=":material/grid_view:",
        )
        business_info = st.Page(
            "pages/master/pg_bussines_info.py",
            title="Business Info",
            icon=":material/business:",
        )

        # Tool & info pages
        upload = st.Page(
            "pages/tools/pg_etls_tools.py",
            title="Data Upload",
            icon=":material/upload:",
        )
        glossarium = st.Page(
            "pages/info/pg_glossarium.py", title="Glossarium", icon=":material/book:"
        )
        profile = st.Page(
            "pages/account/pg_profile.py", title="Profile", icon=":material/person:"
        )

        # ✅ 5. Show authenticated navigation
        nav_structure = {
            "Account": [logout_page],
            "Dashboard": [dashboard, analytics],
            "Reports": [transaction, sellin, visit, transfer, rgu],
            "Master Data": [site, retailer, territory, allocation, business_info],
            "Tools": [upload],
            "Info": [glossarium, profile],
        }

        # Add admin pages if admin
        if is_admin:
            settings = st.Page(
                "pages/admin/pg_sys_settings.py",
                title="Settings",
                icon=":material/settings:",
            )
            nav_structure["Admin"] = [settings]

        # Simple sidebar info
        with st.sidebar:
            st.write(f"👤 **{current_user.name}**")
            st.write(f"🔑 {'Admin' if is_admin else 'User'}")

            if st.button("🔄 Extend Session", use_container_width=True):
                auth_manager.extend_session()
                st.success("Session extended!")
                st.rerun()

        pg = st.navigation(nav_structure)
    else:
        # ✅ 6. Show login-only navigation
        pg = st.navigation([login_page])

    pg.run()


if __name__ == "__main__":
    main()


# NOTE: Following Streamlit official pattern with existing auth architecture
# SIMPLIFIED: Single entry point, functions instead of classes
# KEPT: Cookie persistence, auth business logic, user management
# REMOVED: Complex navigation.py, separate run.py, hidden elements
