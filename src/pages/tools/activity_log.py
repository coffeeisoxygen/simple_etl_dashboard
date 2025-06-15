"""Activity log page untuk monitoring user actions dan audit trail."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
from loguru import logger
from src.config.logging import log_action


def get_audit_database_path() -> Path:
    """Get audit database path."""
    return Path("logs/audit.sqlite")


def load_audit_data(limit: int = 100, hours_back: int = 24) -> pd.DataFrame:
    """Load audit data from SQLite database."""
    db_path = get_audit_database_path()

    if not db_path.exists():
        return pd.DataFrame()

    try:
        conn = sqlite3.connect(str(db_path))

        # Calculate time filter
        cutoff_time = datetime.now() - timedelta(hours=hours_back)

        query = """
            SELECT
                id,
                timestamp,
                level,
                user_id,
                session_id,
                action,
                resource,
                message,
                detail,
                ip_address,
                user_agent,
                created_at
            FROM audit_log
            WHERE datetime(timestamp) >= datetime(?)
            ORDER BY timestamp DESC
            LIMIT ?
        """

        df = pd.read_sql_query(query, conn, params=[cutoff_time.isoformat(), limit])

        conn.close()

        # Convert timestamp to datetime
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["created_at"] = pd.to_datetime(df["created_at"])

        return df

    except Exception as e:
        logger.error(f"Failed to load audit data: {e}")
        return pd.DataFrame()


def get_audit_summary() -> dict:
    """Get audit summary statistics."""
    db_path = get_audit_database_path()

    if not db_path.exists():
        return {
            "total_records": 0,
            "unique_users": 0,
            "unique_sessions": 0,
            "actions_today": 0,
        }

    try:
        conn = sqlite3.connect(str(db_path))

        # Total records
        total_records = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]

        # Unique users
        unique_users = conn.execute(
            "SELECT COUNT(DISTINCT user_id) FROM audit_log WHERE user_id IS NOT NULL"
        ).fetchone()[0]

        # Unique sessions
        unique_sessions = conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM audit_log WHERE session_id IS NOT NULL"
        ).fetchone()[0]

        # Actions today
        today = datetime.utcnow().date()
        actions_today = conn.execute(
            "SELECT COUNT(*) FROM audit_log WHERE date(timestamp) = ?",
            [today.isoformat()],
        ).fetchone()[0]

        conn.close()

        return {
            "total_records": total_records,
            "unique_users": unique_users,
            "unique_sessions": unique_sessions,
            "actions_today": actions_today,
        }

    except Exception as e:
        logger.error(f"Failed to get audit summary: {e}")
        return {
            "total_records": 0,
            "unique_users": 0,
            "unique_sessions": 0,
            "actions_today": 0,
        }


def render_audit_summary() -> None:
    """Render audit summary metrics."""
    st.subheader("📊 Activity Summary")

    summary = get_audit_summary()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Records", summary["total_records"])

    with col2:
        st.metric("Unique Users", summary["unique_users"])

    with col3:
        st.metric("Unique Sessions", summary["unique_sessions"])

    with col4:
        st.metric("Actions Today", summary["actions_today"])


def render_activity_filters() -> tuple[int, int]:
    """Render activity filtering controls."""
    st.subheader("🔍 Filters")

    col1, col2 = st.columns(2)

    with col1:
        hours_back = st.selectbox(
            "Time Range",
            options=[1, 6, 12, 24, 48, 168],  # 1h to 1 week
            index=3,  # Default to 24h
            format_func=lambda x: f"Last {x} hours"
            if x < 24
            else f"Last {x // 24} days",
        )

    with col2:
        limit = st.selectbox(
            "Max Records",
            options=[50, 100, 200, 500, 1000],
            index=1,  # Default to 100
        )

    return hours_back, limit


def render_activity_table(df: pd.DataFrame) -> None:
    """Render activity data table."""
    st.subheader("📋 Activity Log")

    if df.empty:
        st.info("No activity data found for the selected time range.")
        return

    # Format dataframe for display
    display_df = df.copy()

    # Format timestamp
    display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Truncate long messages
    display_df["message"] = display_df["message"].str[:50] + "..."

    # Select columns for display
    columns_to_show = ["timestamp", "level", "user_id", "action", "resource", "message"]
    display_df = display_df[columns_to_show]

    # Show the table
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "timestamp": st.column_config.TextColumn("Time"),
            "level": st.column_config.TextColumn("Level"),
            "user_id": st.column_config.TextColumn("User"),
            "action": st.column_config.TextColumn("Action"),
            "resource": st.column_config.TextColumn("Resource"),
            "message": st.column_config.TextColumn("Message"),
        },
    )

    # Show record count
    st.caption(f"Showing {len(display_df)} records")


def render_activity_details(df: pd.DataFrame) -> None:
    """Render detailed activity information."""
    if df.empty:
        return

    st.subheader("🔍 Activity Details")

    # Select a record to view details
    if len(df) > 0:
        record_options = [
            f"{row['timestamp'].strftime('%H:%M:%S')} - {row['action']} - {row['message'][:30]}..."
            for _, row in df.head(10).iterrows()
        ]

        selected_idx = st.selectbox(
            "Select record to view details:",
            options=range(len(record_options)),
            format_func=lambda x: record_options[x],
        )

        if selected_idx is not None:
            selected_record = df.iloc[selected_idx]

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Basic Information:**")
                st.write(f"**Time:** {selected_record['timestamp']}")
                st.write(f"**Level:** {selected_record['level']}")
                st.write(f"**User:** {selected_record['user_id']}")
                st.write(f"**Action:** {selected_record['action']}")
                st.write(f"**Resource:** {selected_record['resource']}")

            with col2:
                st.write("**Technical Details:**")
                st.write(f"**Session:** {selected_record['session_id']}")
                st.write(f"**IP Address:** {selected_record['ip_address']}")
                st.write(f"**User Agent:** {selected_record['user_agent'][:50]}...")

            st.write("**Message:**")
            st.code(selected_record["message"])

            st.write("**Detail:**")
            st.code(selected_record["detail"])


def render_test_actions() -> None:
    """Render test actions untuk generate sample audit data."""
    st.subheader("🧪 Test Actions")

    st.write("Generate sample audit data untuk testing:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Test Info Action"):
            log_action(
                action="test_info",
                message="Test info action from activity log page",
                resource="activity_log_page",
                detail={"test_type": "info", "timestamp": datetime.now().isoformat()},
            )
            st.success("Info action logged!")

    with col2:
        if st.button("Test Warning Action"):
            log_action(
                action="test_warning",
                message="Test warning action from activity log page",
                resource="activity_log_page",
                detail={
                    "test_type": "warning",
                    "timestamp": datetime.now().isoformat(),
                },
                level="WARNING",
            )
            st.success("Warning action logged!")

    with col3:
        if st.button("Test Error Action"):
            log_action(
                action="test_error",
                message="Test error action from activity log page",
                resource="activity_log_page",
                detail={"test_type": "error", "timestamp": datetime.now().isoformat()},
                level="ERROR",
            )
            st.success("Error action logged!")


def main() -> None:
    """Main activity log page."""
    st.title("📈 Activity Log")

    # Log page access
    log_action(
        action="page_access",
        message="User accessed activity log page",
        resource="activity_log_page",
    )

    # Render summary
    render_audit_summary()

    st.divider()

    # Render filters
    hours_back, limit = render_activity_filters()

    # Load data
    with st.spinner("Loading activity data..."):
        df = load_audit_data(limit=limit, hours_back=hours_back)

    st.divider()

    # Render table
    render_activity_table(df)

    st.divider()

    # Render details
    render_activity_details(df)

    st.divider()

    # Render test actions
    render_test_actions()

    # Auto-refresh option
    if st.checkbox("Auto-refresh (10s)"):
        st.rerun()


if __name__ == "__main__":
    main()
