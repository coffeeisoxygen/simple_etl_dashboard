"""Authentication page with modern GitHub-style design."""

import streamlit as st
from loguru import logger

from schemas.auth.request import LoginRequest
from services.auth_manager import get_auth_manager


@st.fragment
def render_login_form() -> None:
    """Render modern, centered login form with minimal spacing."""
    _col1, col2, _col3 = st.columns([1, 2, 1])
    with col2:
        # ✅ FIX: Remove top margin from container
        st.markdown(
            """
            <div style="
                background: #ffffff;
                padding: 2rem 2.5rem;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 12px 32px rgba(0, 0, 0, 0.05);
                max-width: 400px;
                margin: 0 auto;
                font-family: 'Segoe UI', sans-serif;
            ">
            """,
            unsafe_allow_html=True,
        )

        # Title & Subtitle
        st.markdown(
            """
            <h2 style='text-align: center; margin-bottom: 1rem; color: #1e293b;'>🔐 Login to ETL Dashboard</h2>
            <p style='text-align: center; color: #64748b; font-size: 0.9rem; margin-bottom: 2rem;'>
                Enter your credentials to access the system.
            </p>
            """,
            unsafe_allow_html=True,
        )

        # Login form
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                label_visibility="visible",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                label_visibility="visible",
            )
            submitted = st.form_submit_button(
                "Sign in", use_container_width=True, type="primary"
            )

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password")
                    return

                try:
                    auth_manager = get_auth_manager()
                    login_request = LoginRequest(username=username, password=password)
                    user_response = auth_manager.login_with_persistence(login_request)
                    st.success(f"Welcome, {user_response.name}!")
                    st.rerun()

                except ValueError as e:
                    st.error(f"Login failed: {str(e)}")
                    logger.warning(f"Login attempt failed for username: {username}")
                except Exception as e:
                    st.error("An unexpected error occurred. Please try again.")
                    logger.error(f"Unexpected login error: {e}")

        # Close container
        st.markdown("</div>", unsafe_allow_html=True)


def render_auth_page() -> None:
    """Main auth page with minimal top spacing."""
    auth_manager = get_auth_manager()

    if auth_manager.is_authenticated():
        st.switch_page("pages/dashboard/pg_dashboard.py")
        return

    # ✅ FIX: Enhanced CSS with aggressive spacing removal
    st.markdown(
        """
        <style>
        /* ✅ AGGRESSIVE SPACING REMOVAL */
        .stApp > header {visibility: hidden;}
        .stApp > .main {padding-top: 0rem !important;}
        .stApp > .main > div {padding-top: 0rem !important;}
        .stApp > .main > div > div {padding-top: 0rem !important;}
        .stApp > .main > div > div > div {padding-top: 0rem !important;}
        .stApp > .main > div > div > div > section {padding-top: 0rem !important;}
        .stApp > .main > div > div > div > section > div {padding-top: 1rem !important;}

        /* ✅ Remove default Streamlit margins */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }

        /* ✅ Remove space above first element */
        .element-container:first-child {
            margin-top: 0 !important;
        }

        /* Input fields */
        .stTextInput > div > div > input {
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 0.95rem;
            color: #0f172a;
        }

        .stTextInput > div > div > input::placeholder {
            color: #94a3b8;
        }

        .stTextInput > div > div > input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
        }

        /* Button */
        .stButton > button {
            background-color: #3b82f6;
            border: none;
            color: white;
            border-radius: 8px;
            font-size: 0.95rem;
            padding: 10px;
            font-weight: 600;
            transition: background-color 0.2s ease-in-out;
        }

        .stButton > button:hover {
            background-color: #2563eb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ✅ FIX: No manual spacing - let CSS handle it
    # Remove this line: st.markdown("<br>", unsafe_allow_html=True)

    # Render UI immediately
    render_login_form()

    # Debug (optional) - moved to bottom to not affect spacing
    if st.checkbox("🔧 Debug", key="auth_debug", help="Show debug information"):
        with st.expander("Session Debug Info"):
            st.json(auth_manager.get_session_info())

    # Footer - with controlled spacing
    st.markdown(
        """
        <div style="margin-top: 2rem;">
            <p style='text-align: center; color: #94a3b8; font-size: 0.75rem;'>
                ⓒ 2025 Internal ETL Tool • All rights reserved
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# NOTE: This is authentication page only. Routing handled elsewhere.
# PINNED: Consider adding animated loading state for better UX
# TODO: Add responsive design for mobile devices
