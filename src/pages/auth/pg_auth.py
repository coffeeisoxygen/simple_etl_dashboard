"""Authentication page with proper service integration.

Handles login/logout functionality using established auth service
and user state management patterns.
"""

import streamlit as st
from loguru import logger

from repositories.auth.sql_user_repository import SQLUserRepository
from schemas.auth.request import LoginRequest
from services.auth_service import login as auth_login
from services.user_state import UserState


def render_login_form() -> None:
    """Display login form and handle authentication."""
    st.title("🔐 Login")
    st.markdown("Masukkan kredensial Anda untuk mengakses sistem")

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input(
            "Username", placeholder="Masukkan username", help="Default admin: admin"
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Masukkan password",
            help="Default password: admin123",
        )

        submitted = st.form_submit_button("🚀 Login", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("❌ Username dan password harus diisi")
                return

            try:
                # Use proper auth service
                login_request = LoginRequest(username=username, password=password)
                user_repo = SQLUserRepository()

                # Authenticate user
                user_response = auth_login(login_request, user_repo)

                # Update session state via UserState
                user_state = UserState()
                user_state.login_user(user_response)

                # Success feedback
                st.success(f"✅ Login berhasil! Selamat datang, {user_response.name}")
                logger.info(f"User logged in: {user_response.username}")

                # Trigger rerun to show authenticated state
                st.rerun()

            except ValueError as e:
                st.error(f"❌ Login gagal: {str(e)}")
                logger.warning(f"Failed login attempt for username: {username}")
            except Exception as e:
                st.error("❌ Terjadi kesalahan sistem. Silakan coba lagi.")
                logger.error(f"Login error: {e}")


def render_logout_section() -> None:
    """Display logout section for authenticated users."""
    user_state = UserState()

    # Display user info
    st.success(f"✅ Anda sudah login sebagai: **{user_state.get_user_name()}**")

    # User info in expander
    with st.expander("ℹ️ Informasi User", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Username:** {user_state.get_username()}")
            st.write(f"**User ID:** {user_state.get_user_id()}")

        with col2:
            st.write(f"**Role:** {'Admin' if user_state.is_admin() else 'User'}")
            st.write(
                f"**Status:** {'Aktif' if user_state.is_active() else 'Tidak Aktif'}"
            )

        if login_time := user_state.get_login_timestamp():
            st.write(f"**Login pada:** {login_time.strftime('%d/%m/%Y %H:%M:%S')}")

    # Logout button
    st.markdown("---")

    col1, col2, _ = st.columns([1, 2, 1])
    with col2:
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            try:
                username = user_state.get_username()
                user_state.logout_user()

                st.success("✅ Logout berhasil!")
                logger.info(f"User logged out: {username}")

                # Clear any cached data and rerun
                st.cache_data.clear()
                st.rerun()

            except Exception as e:
                st.error("❌ Terjadi kesalahan saat logout")
                logger.error(f"Logout error: {e}")


def render_auth_page() -> None:
    """Main authentication page renderer.

    Dynamically shows login form or logout section based on authentication status.

    NOTE: Page config is handled at app level, not page level
    """
    user_state = UserState()

    # Check authentication status
    if not user_state.is_authenticated():
        # Show login form
        render_login_form()

        # Login help
        with st.expander("💡 Bantuan Login"):
            st.info(
                """
                **Kredensial Default:**
                - Username: `admin`
                - Password: `admin123`

                **Catatan:**
                - Akun admin dibuat otomatis saat aplikasi pertama kali dijalankan
                - Hubungi administrator jika mengalami masalah login
                """
            )
    else:
        # Show authenticated user section
        st.title("🏠 Dashboard")
        render_logout_section()

        # Navigation hint
        st.markdown("---")
        st.info("✨ Gunakan navigasi untuk mengakses fitur-fitur aplikasi")
