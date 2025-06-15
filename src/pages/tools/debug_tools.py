"""Enhanced debug tools dengan database dan logging info."""

import streamlit as st
from src.models.debug_service import (
    AppStateDebugData,
    ContextDebugData,
    DebugActionService,
    DebugReportGenerator,
    SessionDebugData,
)

st.title("🔧 Debug Tools")

# Create tabs for different debug categories
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "🔐 Session",
        "🌐 Context",
        "📊 State",
        "🗄️ Database",
        "⚡ Actions",
    ]
)

# Tab 1: Session Debug
with tab1:
    st.header("Session & Authentication")

    session_debug = SessionDebugData()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔐 Authentication Status")
        st.json(session_debug.session_info)

        # Session Timeline
        if session_debug.session_info.get("authenticated", False):
            st.subheader("⏱️ Session Timeline")
            timeline = session_debug.get_session_timeline()

            if "login_time" in timeline:
                st.metric("Login Time", timeline["login_time"])

            if "expires_in" in timeline:
                st.metric("Session Expires", timeline["expires_in"])

            if "status" in timeline:
                delta = (
                    "from refresh"
                    if timeline["status"] == "Restored"
                    else "normal login"
                )
                st.metric("Session Status", timeline["status"], delta)

    with col2:
        st.subheader("💾 Persistent Data")
        st.json(session_debug.user_data)

        st.subheader("🌐 Browser Session")
        st.code(session_debug.browser_session_id, language="text")

# Tab 2: Context Information
with tab2:
    st.header("Browser & Environment Context")

    context_debug = ContextDebugData()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌐 Network & URL")
        network_info = context_debug.context_data["network"]
        st.write(f"**App URL:** `{network_info['url']}`")
        st.write(f"**IP Address:** `{network_info['ip_address']}`")
        st.write(f"**Browser:** `{network_info['user_agent']}`")

    with col2:
        st.subheader("🌍 Localization")
        locale_info = context_debug.context_data["localization"]
        st.write(f"**Browser Locale:** `{locale_info['browser_locale']}`")
        st.write(f"**Timezone:** `{locale_info['timezone']}`")
        st.write(f"**Local Time:** `{locale_info['local_time']}`")

    # Cookies section
    st.subheader("🍪 Cookies Analysis")
    cookies = context_debug.context_data["cookies"]
    if cookies:
        for cookie in cookies:
            st.write(
                f"**{cookie['name']}** ({cookie['category']}): `{cookie['value']}`"
            )
            if cookie["description"]:
                st.caption(cookie["description"])
    else:
        st.write("No cookies available")

# Tab 3: Session State
with tab3:
    st.header("Application State")

    app_state_debug = AppStateDebugData()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Session Metrics")
        metrics = app_state_debug.metrics

        st.metric("Debug Page Visits", metrics["debug_page_visits"])

        if metrics["app_initialized"]:
            st.success("✅ App properly initialized")
            if "app_uptime" in metrics:
                st.metric("App Uptime", metrics["app_uptime"])

        st.write(f"**Streamlit Session ID:** `{metrics['streamlit_session_id']}`")

    with col2:
        st.subheader("🔗 URL Parameters")
        query_params = app_state_debug.session_state_info["query_params"]
        if query_params:
            st.write("**Current Query Parameters:**")
            for key, value in query_params.items():
                st.write(f"- `{key}`: `{value}`")
        else:
            st.write("No query parameters in URL")

        st.metric(
            "Total Session Keys", app_state_debug.session_state_info["total_keys"]
        )

    # Full session state view
    if st.button("📊 Show Complete Session State"):
        st.subheader("Complete Session State")
        complete_state = app_state_debug.get_complete_session_state()
        st.json(complete_state)

# Tab 4: Database & Logging
with tab4:
    st.header("Database & Logging Status")

    # Database section
    st.subheader("🗄️ Database Status")
    db_debug = app_state_debug.database_debug

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Connection Status**")
        conn_status = db_debug.connection_status

        if conn_status.get("connected", False):
            st.success("✅ Database Connected")
            st.write(f"Connection: `{conn_status.get('connection_name', 'unknown')}`")
        else:
            st.error("❌ Database Disconnected")
            if "error" in conn_status:
                st.error(f"Error: {conn_status['error']}")

    with col2:
        st.write("**Schema Status**")
        schema_status = db_debug.schema_status

        if schema_status.get("valid", False):
            st.success(
                f"✅ Schema Valid ({schema_status.get('table_count', 0)} tables)"
            )

            if "tables" in schema_status:
                st.write("**Tables:**")
                for table_name, table_info in schema_status["tables"].items():
                    st.write(f"- `{table_name}`: {table_info.get('row_count', 0)} rows")
        else:
            st.error("❌ Schema Issues")
            if "error" in schema_status:
                st.error(f"Error: {schema_status['error']}")

    # Database info details
    if st.button("🔍 Show Database Details"):
        st.json(db_debug.db_info)

    st.divider()

    # Logging section
    st.subheader("📝 Logging Status")
    logging_debug = app_state_debug.logging_debug

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Configuration Status**")
        state_info = logging_debug.state_info

        if state_info.get("fully_configured", False):
            st.success("✅ Logging Fully Configured")
        else:
            st.warning("⚠️ Partial Logging Configuration")

        st.write(
            f"Development: {'✅' if state_info.get('development_configured') else '❌'}"
        )
        st.write(f"Audit: {'✅' if state_info.get('audit_configured') else '❌'}")

        if state_info.get("error_count", 0) > 0:
            st.error(f"Errors: {state_info['error_count']}")
            for error in state_info.get("errors", []):
                st.error(f"- {error}")

    with col2:
        st.write("**Log Files Status**")
        log_files = logging_debug.log_files_status

        for file_name, file_info in log_files.items():
            if file_info["exists"]:
                size_mb = file_info["size"] / (1024 * 1024)
                st.success(f"✅ {file_name} ({size_mb:.2f} MB)")
            else:
                st.warning(f"⚠️ {file_name} (missing)")

# Tab 5: Actions
with tab5:
    st.header("Debug Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🔄 Refresh Actions")

        if st.button("Refresh Page", use_container_width=True):
            st.rerun()

        if st.button("Force Session Restore", use_container_width=True):
            if DebugActionService.force_session_restore():
                st.success("Session restore triggered")
            st.rerun()

    with col2:
        st.subheader("🧹 Clear Actions")

        if st.button("Clear Session State", use_container_width=True):
            removed_count = DebugActionService.clear_session_state()
            st.success(f"Cleared {removed_count} session keys")
            st.rerun()

        if st.button("Clear Authentication", use_container_width=True):
            removed_count = DebugActionService.clear_authentication()
            st.success(f"Cleared {removed_count} auth keys")
            st.rerun()

    with col3:
        st.subheader("🗑️ Reset Actions")

        if st.button("Reset User Data", use_container_width=True):
            if DebugActionService.reset_user_data():
                st.success("User data file deleted")
            else:
                st.info("No user data file found")
            st.rerun()

        if st.button("Copy Session ID", use_container_width=True):
            try:
                from streamlit.runtime.scriptrunner import get_script_run_ctx

                ctx = get_script_run_ctx()
                if ctx:
                    st.code(ctx.session_id, language="text")
                    st.success("Session ID displayed above")
            except Exception as e:
                st.error(f"Cannot retrieve session ID: {str(e)}")

    # Export debug info
    st.subheader("📋 Export Debug Info")
    if st.button("Generate Debug Report", use_container_width=True):
        report_generator = DebugReportGenerator()

        st.download_button(
            label="📥 Download Debug Report",
            data=report_generator.export_as_json(),
            file_name=report_generator.get_filename(),
            mime="application/json",
            use_container_width=True,
        )
