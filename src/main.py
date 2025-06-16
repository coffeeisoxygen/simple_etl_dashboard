"""Main application entry point with clean state management.

This module provides the main Streamlit application with proper initialization
and state management to prevent re-initialization on reruns.
"""

import streamlit as st

from shared.app_state import (
    AppInitializer,
    AppState,
    clear_user_context,
    get_user_context,
    show_state_debug,
)


def page_config() -> None:
    """Set the page configuration for the Streamlit app.

    This function configures the layout, initial sidebar state, and menu items
    for the Streamlit application.
    """
    st.set_page_config(
        page_title="ETL Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://docs.streamlit.io/library/get-help",
            "About": "ETL Dashboard for Business Intelligence",
        },
    )


def show_sidebar() -> None:
    """Show sidebar with navigation and user context."""
    with st.sidebar:
        # Logo/branding
        st.markdown("### 📊 ETL Dashboard")
        st.markdown("---")

        # User context
        user = get_user_context()
        if user["authenticated"]:
            st.success(f"👤 Welcome, {user['username']}")
            if user["is_admin"]:
                st.badge("🔐 Admin")

            # Navigation for authenticated users
            st.markdown("### 🧭 Navigation")
            st.selectbox(
                "Select Page:",
                [
                    "Dashboard",
                    "ETL Pipeline",
                    "Data View",
                    "User Management",
                    "Settings",
                ],
                key="selected_page",
            )

            # Logout button
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                clear_user_context()
                st.rerun()
        else:
            st.info("👋 Please login to access the dashboard")

        # Debug section for business owner
        st.markdown("---")
        if st.checkbox("🔧 Show Debug Info"):
            AppState.set_state("show_debug_info", True)
        else:
            AppState.set_state("show_debug_info", False)


def show_login_page() -> None:
    """Show login page for unauthenticated users."""
    st.title("🔐 Login")
    st.markdown("Please login to access the ETL Dashboard")

    # TODO: Implement actual login form with auth_service
    # For now, show placeholder
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Login Form")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password"
            )

            if st.form_submit_button("Login", use_container_width=True):
                # TODO: Implement actual authentication
                # For now, mock login for testing
                if username == "admin" and password == "admin123":
                    from shared.app_state import set_user_context

                    set_user_context("1", "admin", is_admin=True)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try admin/admin123 for testing.")

        st.markdown("---")
        st.info("💡 **Test Credentials:**\nUsername: `admin`\nPassword: `admin123`")


def show_dashboard() -> None:
    """Show main dashboard for authenticated users."""
    user = get_user_context()

    st.title("📊 ETL Dashboard")
    st.markdown(f"Welcome back, **{user['username']}**! 👋")

    # Dashboard metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📁 Total Files", "0", "No change")

    with col2:
        st.metric("📊 Records Processed", "0", "No change")

    with col3:
        st.metric("⚡ Last ETL Run", "Never", "No data")

    with col4:
        st.metric("🟢 System Status", "Healthy", "All systems operational")

    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 Upload CSV", use_container_width=True):
            st.info("CSV upload feature coming soon!")

    with col2:
        if st.button("▶️ Run ETL", use_container_width=True):
            st.info("ETL pipeline feature coming soon!")

    with col3:
        if st.button("📈 View Reports", use_container_width=True):
            st.info("Reporting feature coming soon!")

    # Recent activity placeholder
    st.markdown("### 📋 Recent Activity")
    st.info("No recent activity to display. Upload a CSV file to get started!")


def show_debug_section() -> None:
    """Show debug information for business owner."""
    if AppState.get_state("show_debug_info", False):
        with st.expander("🔧 Debug Information", expanded=True):
            debug_info = show_state_debug()
            st.json(debug_info)

            # Additional debug controls
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔄 Refresh Debug Info"):
                    st.rerun()

            with col2:
                if st.button("🗑️ Clear Session State"):
                    # Clear non-essential state
                    keys_to_keep = [
                        AppState.LOG_CONFIGURED,
                        AppState.DATABASE_INITIALIZED,
                        AppState.APP_INITIALIZED,
                    ]

                    for key in list(st.session_state.keys()):
                        if key not in keys_to_keep:
                            del st.session_state[key]

                    st.success(
                        "Session state cleared (keeping essential initialization)"
                    )
                    st.rerun()


def main() -> None:
    """Main function to run the Streamlit app with proper initialization."""
    # Configure page first
    page_config()

    # Initialize application stack (one-time only)
    if not AppInitializer.initialize_app():
        st.error("❌ Failed to initialize application. Please check logs.")
        st.code("Check the terminal/console for detailed error messages.")
        st.stop()

    # Show sidebar
    show_sidebar()

    # Main content based on authentication status
    user = get_user_context()

    if not user["authenticated"]:
        # Show login page
        show_login_page()
    else:
        # Show authenticated content
        selected_page = AppState.get_state("selected_page", "Dashboard")

        if selected_page == "Dashboard":
            show_dashboard()
        elif selected_page == "ETL Pipeline":
            st.title("📤 ETL Pipeline")
            st.info("ETL Pipeline features coming soon!")
        elif selected_page == "Data View":
            st.title("📊 Data View")
            st.info("Data visualization features coming soon!")
        elif selected_page == "User Management":
            st.title("👥 User Management")
            if user["is_admin"]:
                st.info("User management features coming soon!")
            else:
                st.error("Admin access required for user management.")
        elif selected_page == "Settings":
            st.title("⚙️ Settings")
            st.info("Settings features coming soon!")

    # Debug section (always available for business owner)
    show_debug_section()


if __name__ == "__main__":
    main()
