"""Activity log page untuk monitoring user actions dan audit trail - File-based logging."""

import re
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from loguru import logger
from src.log_setup import log_activity


class ActivityLogParser:
    """Parser untuk loguru-formatted activity log files."""

    def __init__(self, log_file_path: Path):
        self.log_file_path = log_file_path

    def parse_activity_logs(
        self,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
        limit: int | None = 100,
    ) -> pd.DataFrame:
        """Parse activity log file and return structured data."""
        if not self.log_file_path.exists():
            return pd.DataFrame()

        try:
            # Read log file
            with open(self.log_file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Filter activity logs
            activity_entries = []

            for line in lines:
                parsed_entry = self._parse_log_line(line)
                if parsed_entry:
                    # Apply datetime filtering
                    entry_time = parsed_entry["timestamp"]

                    if start_datetime and entry_time < start_datetime:
                        continue
                    if end_datetime and entry_time > end_datetime:
                        continue

                    activity_entries.append(parsed_entry)

            # Sort by timestamp (newest first) and limit
            activity_entries.sort(key=lambda x: x["timestamp"], reverse=True)
            if limit is not None:
                activity_entries = activity_entries[:limit]

            return (
                pd.DataFrame(activity_entries) if activity_entries else pd.DataFrame()
            )

        except Exception as e:
            logger.error(f"Failed to parse activity logs: {e}")
            return pd.DataFrame()

    def _parse_log_line(self, line: str) -> dict[str, Any] | None:
        """Parse single log line from activity.log format."""
        # FIXED: Correct pattern for activity.log format
        # Format: "2025-06-15 22:31:10 | INFO     | LOGGING_INIT | message"
        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s+\| ([^|]+) \| (.+)"

        match = re.match(pattern, line.strip())
        if not match:
            return None

        timestamp_str, level, action, message = match.groups()

        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

            return {
                "timestamp": timestamp,
                "level": level.strip(),
                "action": action.strip(),
                "message": message.strip(),
                "raw_line": line.strip(),
            }
        except ValueError:
            return None

    def get_activity_summary(
        self,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
    ) -> dict[str, int]:
        """Get activity summary statistics."""
        df = self.parse_activity_logs(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=None,
        )

        if df.empty:
            return {
                "total_activities": 0,
                "unique_actions": 0,
                "activities_today": 0,
                "error_activities": 0,
            }

        today = datetime.now().date()
        today_activities = df[df["timestamp"].dt.date == today]

        return {
            "total_activities": len(df),
            "unique_actions": len(df["action"].unique()),
            "activities_today": len(today_activities),
            "error_activities": len(df[df["level"] == "ERROR"]),
        }


def get_activity_log_path() -> Path:
    """Get activity log file path."""
    return Path("logs/activity.log")


def render_activity_summary(
    parser: ActivityLogParser,
    start_datetime: datetime | None,
    end_datetime: datetime | None,
) -> None:
    """Render activity summary metrics."""
    st.subheader("📊 Activity Summary")

    summary = parser.get_activity_summary(start_datetime, end_datetime)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Activities", summary["total_activities"])

    with col2:
        st.metric("Unique Actions", summary["unique_actions"])

    with col3:
        st.metric("Activities Today", summary["activities_today"])

    with col4:
        st.metric("Error Activities", summary["error_activities"])


def render_datetime_filters() -> tuple[datetime | None, datetime | None, int]:
    """Render enhanced datetime filtering controls."""
    st.subheader("🔍 Filters")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Date Range:**")
        today = datetime.now().date()

        start_date = st.date_input(
            "Start Date",
            value=today - timedelta(days=1),  # Default to yesterday
            max_value=today,
        )

        start_time = st.time_input(
            "Start Time",
            value=time(0, 0),  # Default to 00:00
        )

    with col2:
        st.write("**End Range:**")
        end_date = st.date_input(
            "End Date",
            value=today,
            max_value=today,
        )

        end_time = st.time_input(
            "End Time",
            value=time(23, 59),  # Default to 23:59
        )

    # Combine date and time
    start_datetime = datetime.combine(start_date, start_time) if start_date else None
    end_datetime = datetime.combine(end_date, end_time) if end_date else None

    # Validation
    if start_datetime and end_datetime and start_datetime > end_datetime:
        st.error("❌ Start datetime cannot be after end datetime")
        return None, None, 100

    # Record limit
    col3, col4 = st.columns(2)

    with col3:
        limit = st.selectbox(
            "Max Records",
            options=[50, 100, 200, 500, 1000, None],
            index=1,  # Default to 100
            format_func=lambda x: "No limit" if x is None else str(x),
        )

    with col4:
        # Quick time range buttons
        st.write("**Quick Ranges:**")

        quick_range_col1, quick_range_col2 = st.columns(2)

        with quick_range_col1:
            if st.button("Last Hour"):
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(hours=1)
                st.session_state.filter_start = start_dt
                st.session_state.filter_end = end_dt
                st.rerun()

            if st.button("Last 24h"):
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=1)
                st.session_state.filter_start = start_dt
                st.session_state.filter_end = end_dt
                st.rerun()

        with quick_range_col2:
            if st.button("Today"):
                today = datetime.now().date()
                start_dt = datetime.combine(today, time(0, 0))
                end_dt = datetime.combine(today, time(23, 59))
                st.session_state.filter_start = start_dt
                st.session_state.filter_end = end_dt
                st.rerun()

            if st.button("Last 7 days"):
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=7)
                st.session_state.filter_start = start_dt
                st.session_state.filter_end = end_dt
                st.rerun()

    # Use session state values if available
    if hasattr(st.session_state, "filter_start"):
        start_datetime = st.session_state.filter_start
    if hasattr(st.session_state, "filter_end"):
        end_datetime = st.session_state.filter_end

    # FIXED: Ensure limit is always int, never None
    if limit is None:
        limit = 1000  # Default to 1000 when "No limit" is selected

    return start_datetime, end_datetime, limit


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
    display_df["message_short"] = display_df["message"].str[:50] + "..."

    # Select columns for display
    columns_to_show = ["timestamp", "level", "action", "message_short"]
    display_df = display_df[columns_to_show]

    # Show the table
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "timestamp": st.column_config.TextColumn("Time", width="medium"),
            "level": st.column_config.TextColumn("Level", width="small"),
            "action": st.column_config.TextColumn("Action", width="medium"),
            "message_short": st.column_config.TextColumn("Message", width="large"),
        },
    )

    # Show record count
    st.caption(f"Showing {len(display_df)} activity records")


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
                st.write(f"**Action:** {selected_record['action']}")

            with col2:
                st.write("**Technical Details:**")
                st.write("**Message Type:** Activity Log")
                st.write("**Source:** File-based logging")

            st.write("**Full Message:**")
            st.code(selected_record["message"])

            st.write("**Raw Log Entry:**")
            st.code(selected_record["raw_line"])


def render_controls() -> None:
    """Render control buttons."""
    st.subheader("🎛️ Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            # Clear any cached data
            if hasattr(st.session_state, "last_refresh"):
                del st.session_state.last_refresh
            st.rerun()

    with col2:
        if st.button("🧹 Clear Filters", use_container_width=True):
            # Clear filter session state
            keys_to_clear = ["filter_start", "filter_end"]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    with col3:
        auto_refresh = st.checkbox("⏱️ Auto-refresh (30s)")
        if auto_refresh:
            st.rerun()


def render_test_actions() -> None:
    """Render test actions untuk generate sample activity data."""
    st.subheader("🧪 Test Actions")

    st.write("Generate sample activity data untuk testing:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Test Info Action"):
            log_activity(
                "TEST_INFO",
                "Test info action from activity log page",
                test_type="info",
                timestamp=datetime.now().isoformat(),
            )
            st.success("Info action logged!")

    with col2:
        if st.button("Test Navigation"):
            log_activity(
                "TEST_NAVIGATION",
                "Test navigation action from activity log page",
                test_type="navigation",
                page="activity_log",
            )
            st.success("Navigation action logged!")

    with col3:
        if st.button("Test User Action"):
            log_activity(
                "TEST_USER_ACTION",
                "Test user action from activity log page",
                test_type="user_action",
                user_id=st.session_state.get("username", "demo_user"),
            )
            st.success("User action logged!")


def main() -> None:
    """Main activity log page."""
    st.title("📈 Activity Log")

    # FIXED: Only log page access once per session to avoid infinite loop
    if not st.session_state.get("activity_page_accessed", False):
        log_activity(
            "PAGE_ACCESS",
            "User accessed activity log page",
            page="activity_log",
            user_id=st.session_state.get("username", "demo_user"),
        )
        st.session_state.activity_page_accessed = True

    # Initialize parser
    log_file_path = get_activity_log_path()
    parser = ActivityLogParser(log_file_path)

    # Check if log file exists
    if not log_file_path.exists():
        st.warning(
            "📁 Activity log file not found. Activity logging may not be configured properly."
        )
        st.info(f"Expected location: `{log_file_path.resolve()}`")
        return

    # Render datetime filters
    start_datetime, end_datetime, limit = render_datetime_filters()

    # Skip processing if validation failed
    if start_datetime is None and end_datetime is None and limit == 100:
        return

    st.divider()

    # Render summary
    render_activity_summary(parser, start_datetime, end_datetime)

    st.divider()

    # Load data
    with st.spinner("Loading activity data..."):
        df = parser.parse_activity_logs(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            limit=limit,
        )

    # Render table
    render_activity_table(df)

    st.divider()

    # Render details
    render_activity_details(df)

    st.divider()

    # Render controls
    render_controls()

    st.divider()

    # Render test actions
    render_test_actions()


if __name__ == "__main__":
    main()
