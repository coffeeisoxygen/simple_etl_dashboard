"""Admin system settings and utilities page.

Multi-tab administration interface providing user management, database monitoring,
system configuration, and debugging tools. Only accessible by admin users.
"""

# ruff : noqa
import streamlit as st
from datetime import datetime
from loguru import logger

from services.auth_manager import get_auth_manager
from services.auth_service import register, change_password, deactivate_user
from repositories.auth.sql_user_repository import SQLUserRepository
from schemas.auth.request import RegisterUserRequest, ChangePasswordRequest
from db.database import get_database_status, get_sql_manager, query_data
from models.user_model import User


def render_user_management_tab() -> None:
    """Render user management tab with full CRUD operations."""
    st.markdown("## 👥 User Management")

    # User registration section
    st.markdown("### ➕ Register New User")

    with st.form("register_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input(
                "Username",
                placeholder="Enter username",
                help="Unique username for login",
            )
            new_name = st.text_input(
                "Full Name",
                placeholder="Enter full name",
                help="Display name for the user",
            )

        with col2:
            new_password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password",
                help="Initial password (user can change later)",
            )

            user_role_col1, user_role_col2 = st.columns(2)
            with user_role_col1:
                is_admin = st.checkbox("Admin User", help="Grant admin privileges")
            with user_role_col2:
                is_active = st.checkbox(
                    "Active", value=True, help="User account status"
                )

        submitted = st.form_submit_button(
            "➕ Create User", use_container_width=True, type="primary"
        )

        if submitted:
            # Validation
            if not all([new_username, new_name, new_password]):
                st.error("❌ All fields are required")
                return

            if len(new_password) < 6:
                st.error("❌ Password must be at least 6 characters")
                return

            try:
                # Register user using existing service
                register_request = RegisterUserRequest(
                    username=new_username.strip(),
                    name=new_name.strip(),
                    password=new_password,
                    is_admin=is_admin,
                    is_active=is_active,
                )

                user_repo = SQLUserRepository()
                register(register_request, user_repo)

                st.success(f"✅ User '{new_username}' created successfully!")
                logger.info(f"Admin created new user: {new_username}")
                st.rerun()

            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                logger.error(f"Failed to create user: {e}")
                st.error("❌ Failed to create user. Please try again.")

    st.markdown("---")

    # User statistics
    st.markdown("### 📊 User Statistics")

    try:
        user_stats = query_data(
            """
            SELECT
                COUNT(*) as total_users,
                SUM(CASE WHEN is_admin = 1 THEN 1 ELSE 0 END) as admin_count,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_count,
                SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive_count
            FROM users
        """,
            ttl=30,
        )

        if not user_stats.empty:
            stats = user_stats.iloc[0]

            # Display user metrics
            metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)

            with metrics_col1:
                st.metric("Total Users", int(stats["total_users"]))

            with metrics_col2:
                st.metric("Admins", int(stats["admin_count"]))

            with metrics_col3:
                st.metric("Active", int(stats["active_count"]))

            with metrics_col4:
                st.metric("Inactive", int(stats["inactive_count"]))

    except Exception as e:
        logger.error(f"Failed to load user statistics: {e}")
        st.error("❌ Failed to load user statistics")

    st.markdown("---")

    # User management table
    st.markdown("### 👤 Manage Users")

    try:
        # Load users with action buttons
        users_df = query_data(
            """
            SELECT
                id, username, name, is_admin, is_active,
                created_at, updated_at
            FROM users
            ORDER BY created_at DESC
        """,
            ttl=60,
        )

        if not users_df.empty:
            # Display user table with actions
            for idx, user in users_df.iterrows():
                with st.container():
                    user_col1, user_col2, user_col3, user_col4 = st.columns(
                        [2, 2, 1, 3]
                    )

                    with user_col1:
                        admin_badge = "🔑 Admin" if user["is_admin"] else "👤 User"
                        status_badge = (
                            "✅ Active" if user["is_active"] else "❌ Inactive"
                        )
                        st.markdown(f"**{user['name']}** ({user['username']})")
                        st.caption(f"{admin_badge} • {status_badge}")

                    with user_col2:
                        st.caption(f"ID: {user['id']}")
                        st.caption(f"Created: {user['created_at'][:10]}")

                    with user_col3:
                        # Status toggle
                        if user["is_active"]:
                            if st.button(
                                "🚫 Deactivate",
                                key=f"deactivate_{user['id']}",
                                help="Deactivate user",
                            ):
                                try:
                                    if user["is_admin"]:
                                        st.error("❌ Cannot deactivate admin users")
                                    else:
                                        user_repo = SQLUserRepository()
                                        deactivate_user(user["id"], user_repo)
                                        st.success(
                                            f"✅ User '{user['username']}' deactivated"
                                        )
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to deactivate user: {e}")
                        else:
                            if st.button(
                                "✅ Activate",
                                key=f"activate_{user['id']}",
                                help="Activate user",
                            ):
                                try:
                                    user_repo = SQLUserRepository()
                                    user_model = user_repo.get_by_id(user["id"])
                                    if user_model:
                                        user_model.is_active = True
                                        user_repo.update(user_model)
                                        st.success(
                                            f"✅ User '{user['username']}' activated"
                                        )
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to activate user: {e}")

                    with user_col4:
                        action_col1, action_col2, action_col3 = st.columns(3)

                        with action_col1:
                            # Toggle admin status
                            if user["is_admin"]:
                                if st.button(
                                    "👤 Remove Admin",
                                    key=f"remove_admin_{user['id']}",
                                    help="Remove admin privileges",
                                ):
                                    try:
                                        user_repo = SQLUserRepository()
                                        user_model = user_repo.get_by_id(user["id"])
                                        if user_model:
                                            user_model.is_admin = False
                                            user_repo.update(user_model)
                                            st.success(
                                                f"✅ Admin privileges removed from '{user['username']}'"
                                            )
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to update user: {e}")
                            else:
                                if st.button(
                                    "🔑 Make Admin",
                                    key=f"make_admin_{user['id']}",
                                    help="Grant admin privileges",
                                ):
                                    try:
                                        user_repo = SQLUserRepository()
                                        user_model = user_repo.get_by_id(user["id"])
                                        if user_model:
                                            user_model.is_admin = True
                                            user_repo.update(user_model)
                                            st.success(
                                                f"✅ '{user['username']}' is now an admin"
                                            )
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to update user: {e}")

                        with action_col2:
                            # Reset password
                            if st.button(
                                "🔐 Reset Password",
                                key=f"reset_pwd_{user['id']}",
                                help="Reset user password",
                            ):
                                # Create a mini form for password reset
                                with st.popover("Reset Password"):
                                    st.markdown(
                                        f"**Reset password for: {user['username']}**"
                                    )
                                    new_pwd = st.text_input(
                                        "New Password",
                                        type="password",
                                        key=f"new_pwd_{user['id']}",
                                    )
                                    if st.button(
                                        "💾 Reset", key=f"confirm_reset_{user['id']}"
                                    ):
                                        if len(new_pwd) >= 6:
                                            try:
                                                user_repo = SQLUserRepository()
                                                user_model = user_repo.get_by_id(
                                                    user["id"]
                                                )
                                                if user_model:
                                                    from utils.hashing import (
                                                        hash_password,
                                                    )

                                                    user_model.password_hash = (
                                                        hash_password(new_pwd)
                                                    )
                                                    user_repo.update(user_model)
                                                    st.success(
                                                        f"✅ Password reset for '{user['username']}'"
                                                    )
                                                    st.rerun()
                                            except Exception as e:
                                                st.error(
                                                    f"❌ Failed to reset password: {e}"
                                                )
                                        else:
                                            st.error(
                                                "❌ Password must be at least 6 characters"
                                            )

                        with action_col3:
                            # User details
                            if st.button(
                                "📋 Details",
                                key=f"details_{user['id']}",
                                help="View user details",
                            ):
                                with st.popover("User Details"):
                                    st.json(
                                        {
                                            "id": user["id"],
                                            "username": user["username"],
                                            "name": user["name"],
                                            "is_admin": bool(user["is_admin"]),
                                            "is_active": bool(user["is_active"]),
                                            "created_at": user["created_at"],
                                            "updated_at": user["updated_at"],
                                        }
                                    )

                    st.markdown("---")
        else:
            st.info("No users found")

    except Exception as e:
        logger.error(f"Failed to load user list: {e}")
        st.error("❌ Failed to load user list")


def render_database_management_tab() -> None:
    """Render database management and monitoring tab."""
    st.markdown("## 🗄️ Database Management")

    # Database health section
    st.markdown("### 💚 Database Health")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Check Database Health", use_container_width=True):
            with st.spinner("Checking database..."):
                health_status = get_database_status()

                if health_status.get("status") == "healthy":
                    st.success("✅ Database is healthy")

                    # Display metrics
                    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

                    with metrics_col1:
                        st.metric(
                            "User Count",
                            health_status.get("user_count", 0),
                            help="Total users in system",
                        )

                    with metrics_col2:
                        st.metric(
                            "DB Size",
                            f"{health_status.get('file_size_mb', 0)} MB",
                            help="Database file size",
                        )

                    with metrics_col3:
                        connection_status = (
                            "Connected"
                            if health_status.get("connection") == "ok"
                            else "Failed"
                        )
                        st.metric(
                            "Connection",
                            connection_status,
                            help="Database connection status",
                        )

                    # Detailed info in expander
                    with st.expander("📊 Detailed Database Info"):
                        st.json(health_status)

                else:
                    st.error("❌ Database health check failed")
                    st.error(health_status.get("error", "Unknown error"))

    with col2:
        st.markdown("**📥 Backup & Recovery**")

        # Last backup info (mockup)
        st.info("🔄 Last backup: 2024-01-15 14:30:00 (Auto)")

        backup_col1, backup_col2 = st.columns(2)

        with backup_col1:
            if st.button("💾 Create Backup", use_container_width=True):
                # TODO: Implement backup functionality
                st.warning("🚧 Backup feature coming soon!")
                st.info("Will create: `backup_2024-01-20_15-30.sqlite`")

        with backup_col2:
            if st.button("📂 Restore Backup", use_container_width=True):
                # TODO: Implement restore functionality
                st.warning("🚧 Restore feature coming soon!")
                st.info("Will show backup file selector")

    st.markdown("---")

    # SQL Query Tester
    st.markdown("### 📊 SQL Query Tester")

    st.markdown("**Execute custom SQL queries (READ-ONLY for safety)**")

    query_input = st.text_area(
        "SQL Query",
        placeholder="SELECT * FROM users LIMIT 10;",
        help="Only SELECT queries allowed for safety",
        height=100,
    )

    if st.button("▶️ Execute Query", use_container_width=True):
        if query_input.strip().upper().startswith("SELECT"):
            try:
                result_df = query_data(query_input, ttl=0)
                st.success(f"✅ Query executed: {len(result_df)} rows returned")
                if not result_df.empty:
                    st.dataframe(result_df, use_container_width=True)
                else:
                    st.info("Query returned no results")
            except Exception as e:
                st.error(f"❌ Query failed: {e}")
        else:
            st.error("❌ Only SELECT queries are allowed for safety")


def render_system_configuration_tab() -> None:
    """Render system configuration tab (mostly mockup for planning)."""
    st.markdown("## ⚙️ System Configuration")

    # Configuration tabs
    config_tab1, config_tab2, config_tab3 = st.tabs(
        ["🔧 General Settings", "🔐 Security Settings", "📊 Performance Settings"]
    )

    with config_tab1:
        st.markdown("### Application Settings")

        # Mockup configuration options
        app_name = st.text_input(
            "Application Name", value="ETL Dashboard", disabled=True
        )
        st.caption("🚧 Configuration editing coming soon")

        timezone = st.selectbox(
            "Timezone",
            ["Asia/Jakarta", "UTC", "Asia/Singapore"],
            index=0,
            disabled=True,
        )

        max_upload_size = st.slider("Max Upload Size (MB)", 1, 100, 50, disabled=True)

        if st.button("💾 Save General Settings", disabled=True):
            st.warning("🚧 Feature coming soon!")

    with config_tab2:
        st.markdown("### Security Configuration")

        # Mockup security settings
        session_timeout = st.slider(
            "Session Timeout (minutes)", 15, 480, 60, disabled=True
        )

        force_password_change = st.checkbox(
            "Force password change on first login", disabled=True
        )

        enable_2fa = st.checkbox("Enable Two-Factor Authentication", disabled=True)

        if st.button("🔐 Save Security Settings", disabled=True):
            st.warning("🚧 Feature coming soon!")

    with config_tab3:
        st.markdown("### Performance & Caching")

        # Mockup performance settings
        cache_ttl = st.slider(
            "Default Cache TTL (seconds)", 30, 3600, 300, disabled=True
        )

        max_concurrent_users = st.slider(
            "Max Concurrent Users", 5, 100, 25, disabled=True
        )

        if st.button("⚡ Save Performance Settings", disabled=True):
            st.warning("🚧 Feature coming soon!")


def render_maintenance_debug_tab() -> None:
    """Render system maintenance and debugging tab."""
    st.markdown("## 🔧 Maintenance & Debug")

    # Maintenance actions
    st.markdown("### 🧹 System Maintenance")

    maint_col1, maint_col2 = st.columns(2)

    with maint_col1:
        st.markdown("**Cleanup Operations**")

        if st.button("🗑️ Clear Application Cache", use_container_width=True):
            # Real implementation for Streamlit cache
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success("✅ Application cache cleared!")

        if st.button("📝 Clear Session Logs", use_container_width=True):
            # TODO: Implement log cleanup
            st.warning("🚧 Log cleanup coming soon!")
            st.info("Will clear logs older than 30 days")

        if st.button("🔄 Restart Services", use_container_width=True):
            # TODO: Implement service restart
            st.warning("🚧 Service restart coming soon!")
            st.info("Will restart background services")

    with maint_col2:
        st.markdown("**System Monitoring**")

        # Current time and uptime (real)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.info(f"🕐 Current Time: {current_time}")

        # Mockup system metrics
        if st.button("📈 View Performance Metrics", use_container_width=True):
            st.warning("🚧 Performance monitoring coming soon!")

            # Mockup metrics display
            mock_col1, mock_col2, mock_col3 = st.columns(3)

            with mock_col1:
                st.metric("CPU Usage", "23%", "2%")

            with mock_col2:
                st.metric("Memory Usage", "156 MB", "12 MB")

            with mock_col3:
                st.metric("Active Sessions", "3", "1")

        if st.button("📋 Export System Report", use_container_width=True):
            # TODO: Implement system report export
            st.warning("🚧 System reporting coming soon!")
            st.info("Will generate comprehensive system health report")

    st.markdown("---")

    # Debug tools section
    st.markdown("### 🐛 Debug Tools")

    debug_col1, debug_col2 = st.columns(2)

    with debug_col1:
        with st.expander("🔍 Session Information", expanded=False):
            # Real session debugging
            auth_manager = get_auth_manager()
            session_info = auth_manager.get_session_info()
            st.json(session_info)

    with debug_col2:
        with st.expander("🗄️ Database Connection Test", expanded=False):
            # Real database debugging
            if st.button("Test Database Connection"):
                try:
                    sql_manager = get_sql_manager()
                    health = sql_manager.health_check()

                    if health.get("status") == "healthy":
                        st.success("✅ Database connection successful")
                        st.json(health)
                    else:
                        st.error("❌ Database connection failed")
                        st.error(health.get("error", "Unknown error"))

                except Exception as e:
                    st.error(f"❌ Connection test failed: {e}")


def render_system_settings_page() -> None:
    """Main system settings page with multi-tab organization."""
    # Require admin authentication
    auth_manager = get_auth_manager()
    auth_manager.require_admin_access()

    st.title("⚙️ Admin System Settings")
    st.markdown("Comprehensive administration interface for system management")
    st.markdown("---")

    # Multi-tab interface
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "👥 User Management",
            "🗄️ Database",
            "⚙️ Configuration",
            "🔧 Maintenance & Debug",
        ]
    )

    with tab1:
        render_user_management_tab()

    with tab2:
        render_database_management_tab()

    with tab3:
        render_system_configuration_tab()

    with tab4:
        render_maintenance_debug_tab()

    # Footer with important notes
    st.markdown("---")
    st.info(
        "🚧 **Development Note**: Features marked with 🚧 are planned for future implementation. "
        "Current version includes user management, monitoring and debugging tools."
    )


# Main execution
if __name__ == "__main__":
    render_system_settings_page()


# TODO: Implement database backup and restore functionality
# TODO: Add system configuration persistence (settings table)
# TODO: Implement log management and cleanup
# TODO: Add performance monitoring and metrics collection
# TODO: Implement service restart and health check endpoints
# PINNED: Add scheduled backup automation
# PINNED: Add system alert and notification system
# REMINDER: All user management actions should be logged for audit
# NOTE: Tab organization improves UX and reduces cognitive load
# FUTURE: Add integration with external monitoring tools
# FUTURE: Add API endpoints for programmatic access
