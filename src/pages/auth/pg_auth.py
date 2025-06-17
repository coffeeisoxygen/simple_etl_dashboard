"""Authentication page with clean, focused authentication logic."""

import streamlit as st
from loguru import logger

from repositories.auth.sql_user_repository import SQLUserRepository
from schemas.auth.request import LoginRequest
from services.auth_service import login as auth_login
from services.user_state import UserState


@st.fragment
def render_login_form() -> None:
    """Display login form and handle authentication."""
    st.title("🔐 Login")
    st.markdown("Masukkan kredensial Anda untuk mengakses sistem")

    with st.form("login_form", clear_on_submit=False):
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
                # Show loading state
                with st.spinner("🔄 Memverifikasi kredensial..."):
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

                # ✅ IMMEDIATE REDIRECT - no delay, no complex state
                st.rerun()

            except ValueError as e:
                st.error(f"❌ Login gagal: {str(e)}")
                logger.warning(f"Failed login attempt for username: {username}")
            except Exception as e:
                st.error("❌ Terjadi kesalahan sistem. Silakan coba lagi.")
                logger.error(f"Login error: {e}")


def render_auth_page() -> None:
    """Clean authentication page - ONLY handles login."""
    user_state = UserState()

    # ✅ SIMPLE: Just check if authenticated
    if user_state.is_authenticated():
        # User sudah login, redirect
        st.info("🔄 Already logged in, redirecting...")
        st.rerun()
        return

    # Show login form
    render_login_form()

    # Login help (static content)
    with st.expander("💡 Bantuan Login"):
        st.info(
            """
            **Kredensial Default:**
            - Username: `admin`
            - Password: `admin123`

            **Catatan:**
            - Akun admin dibuat otomatis saat aplikasi pertama kali dijalankan
            - Hubungi administrator jika mengalama masalah login
            """
        )
