from datetime import UTC, datetime

import streamlit as st
from loguru import logger

try:
    import pytz
except ImportError:
    pytz = None

st.title("🔍 Context Information")

# User Context Information
st.header("User Context Information")

col1, col2 = st.columns(2)

with col1:
    st.subheader("**URL & Network Info:**")
    st.write(f"App URL: `{st.context.url}`")

    if st.context.ip_address:
        st.write(f"IP Address: `{st.context.ip_address}`")
        logger.debug(f"User IP: {st.context.ip_address}")
    else:
        st.write("IP Address: `localhost (development)`")

    # Headers yang berguna
    user_agent = st.context.headers.get("user-agent", "Not available")
    if user_agent != "Not available":
        browser_info = (
            user_agent.split(")")[0] + ")"
            if ") " in user_agent
            else user_agent[:50] + "..."
        )
        st.write(f"Browser: `{browser_info}`")

with col2:
    st.subheader("**Localization Info:**")
    st.write(f"Browser Locale: `{st.context.locale}`")
    st.write(f"Timezone: `{st.context.timezone}`")

    if pytz:
        try:
            timezone_str = st.context.timezone or "UTC"
            tz = pytz.timezone(timezone_str)
            utc_now = datetime.now(UTC)
            local_time = utc_now.astimezone(tz)
            st.write(f"Local Time: `{local_time.strftime('%Y-%m-%d %H:%M:%S')}`")
        except Exception as e:
            st.write(f"Local Time: Unable to calculate ({str(e)})")
    else:
        st.write("Local Time: pytz not available")

# Cookies analysis
st.header("🍪 Cookies Analysis")

if st.context.cookies:
    for cookie_name, cookie_value in st.context.cookies.items():
        display_value = (
            cookie_value[:50] + "..." if len(cookie_value) > 50 else cookie_value
        )

        if cookie_name == "ajs_anonymous_id":
            st.write(f"**{cookie_name}** (Analytics): `{display_value}`")
            st.caption("🔍 Segment.io analytics tracking")
        elif cookie_name.startswith("Hm_"):
            st.write(f"**{cookie_name}** (Baidu Analytics): `{display_value}`")
            st.caption("🔍 Baidu Analytics service")
        elif cookie_name == "_streamlit_xsrf":
            st.write(f"**{cookie_name}** (Security): `{display_value}`")
            st.caption("🔒 CSRF protection token")
        else:
            st.write(f"**{cookie_name}**: `{display_value}`")
else:
    st.write("No cookies available")

# Session Information
st.header("📋 Session Information")

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    ctx = get_script_run_ctx()
    if ctx:
        session_id = ctx.session_id
        st.write(f"Session ID: `{session_id}`")
        logger.debug(f"Session ID retrieved: {session_id}")
except Exception as e:
    st.write(f"Session ID: Unable to retrieve ({str(e)})")

# Initialize session state untuk demo
if "counter" not in st.session_state:
    st.session_state.counter = 0

if "user_settings" not in st.session_state:
    st.session_state.user_settings = {"theme": "light", "language": "id"}

# Counter demo
st.session_state.counter += 1
st.write(f"Page loaded {st.session_state.counter} times in this session")

# App initialization info
if hasattr(st.session_state, "app_initialized") and st.session_state.app_initialized:
    st.success("✅ App properly initialized")
    if hasattr(st.session_state, "app_start_time"):
        duration = datetime.now() - st.session_state.app_start_time
        st.write(f"App running for: {duration}")

# Query Parameters
st.header("🔗 URL Query Parameters")

if st.query_params:
    st.write("**Current Query Parameters:**")
    for key, value in st.query_params.items():
        st.write(f"- `{key}`: `{value}`")
else:
    st.write("No query parameters in URL")

# Quick actions
st.header("⚡ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Context"):
        st.rerun()

with col2:
    if st.button("📋 Copy Session ID"):
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx

            ctx = get_script_run_ctx()
            if ctx:
                st.code(ctx.session_id)
        except:
            st.error("Cannot retrieve session ID")

with col3:
    if st.button("🧹 Clear Session"):
        keys_to_clear = [
            k
            for k in st.session_state.keys()
            if k not in ["app_initialized", "app_start_time", "logged_in"]
        ]
        for key in keys_to_clear:
            del st.session_state[key]
        st.success("Session cleared (except critical keys)")
        st.rerun()
