"""User profile page for viewing and updating account information."""

import streamlit as st
from loguru import logger

from repositories.auth.sql_user_repository import SQLUserRepository
from schemas.auth.request import ChangePasswordRequest
from services.auth_manager import get_auth_manager
from services.auth_service import change_password


def render_profile_info() -> None:
    """Display current user profile information."""
    auth_manager = get_auth_manager()
    current_user = auth_manager.get_current_user()

    if not current_user:
        st.error("❌ Unable to load profile information")
        return

    st.markdown("### 👤 Profile Information")

    # Display profile in a clean card format
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**📧 Username:**")
        st.markdown("**👤 Full Name:**")
        st.markdown("**🔑 Role:**")
        st.markdown("**✅ Status:**")
        st.markdown("**🆔 User ID:**")

    with col2:
        st.markdown(f"`{current_user.username}`")
        st.markdown(f"`{current_user.name}`")
        st.markdown(f"`{'Administrator' if current_user.is_admin else 'User'}`")
        st.markdown(f"`{'Active' if current_user.is_active else 'Inactive'}`")
        st.markdown(f"`{current_user.id}`")


def render_update_name_section() -> None:
    """Render the update name form section."""
    auth_manager = get_auth_manager()
    current_user = auth_manager.get_current_user()

    if not current_user:
        return

    st.markdown("### ✏️ Update Name")

    with st.form("update_name_form", clear_on_submit=False):
        st.markdown("**Change your display name:**")
        new_name = st.text_input(
            "New Name",
            value=current_user.name,
            placeholder="Enter your new display name",
        )

        submitted = st.form_submit_button("💾 Update Name", use_container_width=True)

        if submitted:
            if not new_name or new_name.strip() == "":
                st.error("❌ Name cannot be empty")
                return

            if new_name.strip() == current_user.name:
                st.warning("⚠️ New name is same as current name")
                return

            try:
                # Update name using repository directly (since we don't have update_name service yet)
                user_repo = SQLUserRepository()
                user_model = user_repo.get_by_id(current_user.id)

                if user_model:
                    user_model.name = new_name.strip()
                    user_repo.update(user_model)

                    # Update session with new name
                    updated_user = auth_manager.get_current_user()
                    if updated_user:
                        # Force refresh by clearing and re-authenticating
                        auth_manager.user_state.logout_user()
                        auth_manager.user_state.login_user(updated_user)

                    st.success(f"✅ Name updated to: {new_name.strip()}")
                    st.rerun()
                else:
                    st.error("❌ Failed to update name - user not found")

            except Exception as e:
                logger.error(f"Failed to update user name: {e}")
                st.error("❌ Failed to update name. Please try again.")


def render_change_password_section() -> None:
    """Render the change password form section."""
    auth_manager = get_auth_manager()
    current_user = auth_manager.get_current_user()

    if not current_user:
        return

    st.markdown("### 🔐 Change Password")

    with st.form("change_password_form", clear_on_submit=True):
        st.markdown("**Update your account password:**")

        old_password = st.text_input(
            "Current Password",
            type="password",
            placeholder="Enter your current password",
        )

        new_password = st.text_input(
            "New Password", type="password", placeholder="Enter your new password"
        )

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            placeholder="Confirm your new password",
        )

        submitted = st.form_submit_button(
            "🔑 Change Password", use_container_width=True
        )

        if submitted:
            # Validation
            if not all([old_password, new_password, confirm_password]):
                st.error("❌ All password fields are required")
                return

            if new_password != confirm_password:
                st.error("❌ New passwords do not match")
                return

            if len(new_password) < 6:
                st.error("❌ New password must be at least 6 characters")
                return

            if old_password == new_password:
                st.warning("⚠️ New password must be different from current password")
                return

            try:
                # Use auth service to change password
                password_request = ChangePasswordRequest(
                    id=current_user.id,
                    old_password=old_password,
                    new_password=new_password,
                )

                user_repo = SQLUserRepository()
                change_password(password_request, user_repo)

                st.success("✅ Password changed successfully!")
                logger.info(f"Password changed for user: {current_user.username}")

            except ValueError as e:
                st.error(f"❌ {str(e)}")
            except Exception as e:
                logger.error(
                    f"Failed to change password for user {current_user.username}: {e}"
                )
                st.error("❌ Failed to change password. Please try again.")


def render_session_info_section() -> None:
    """Render session and debug information section."""
    auth_manager = get_auth_manager()

    with st.expander("🔧 Session & Debug Information"):
        st.markdown("**Session Status:**")

        # Session timeout info
        timeout_info = auth_manager.get_session_timeout_info()
        if timeout_info:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Session Age",
                    f"{timeout_info['session_age_minutes']} min",
                    help="How long you've been logged in",
                )

            with col2:
                st.metric(
                    "Time Remaining",
                    f"{timeout_info['time_remaining_minutes']} min",
                    help="Time until session expires",
                )

            with col3:
                if st.button("🔄 Extend Session", help="Reset session timeout"):
                    if auth_manager.extend_session():
                        st.success("✅ Session extended!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to extend session")

        # Cookie info
        st.markdown("**Storage Information:**")
        cookie_info = auth_manager.cookie_service.get_info()
        st.json(cookie_info)


def render_profile_page() -> None:
    """Main profile page rendering function."""
    # Require authentication
    auth_manager = get_auth_manager()
    auth_manager.require_authentication()

    st.title("👤 User Profile")
    st.markdown("Manage your account information and settings")
    st.markdown("---")

    # Profile Information Section
    render_profile_info()

    st.markdown("---")

    # Update sections in tabs for better organization
    tab1, tab2 = st.tabs(["✏️ Update Profile", "🔐 Change Password"])

    with tab1:
        render_update_name_section()

    with tab2:
        render_change_password_section()

    st.markdown("---")

    # Session info section
    render_session_info_section()


# Main execution
if __name__ == "__main__":
    render_profile_page()


# TODO: Add profile picture upload functionality
# PINNED: Add user activity log/history
# REMINDER: Name updates require session refresh to show immediately
# NOTE: Password changes use existing auth_service with proper validation
