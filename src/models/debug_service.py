"""Debug service classes dengan database integration yang baru."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import streamlit as st
from loguru import logger
from src.authentication import get_session_info
from src.config.logging import LoggingState, get_logging_status
from src.database import DatabaseManager, get_database_manager


class SessionDebugData:
    """Session dan authentication debug information."""

    def __init__(self) -> None:
        self.session_info = get_session_info()
        self.user_data = self._load_user_data()
        self.browser_session_id = self._get_browser_session_id()

    def _load_user_data(self) -> dict[str, Any]:
        """Load user data from persistent storage."""
        try:
            from src.authentication import _get_managers

            user_manager, _ = _get_managers()
            return user_manager.load_user_data().to_dict()
        except Exception as e:
            logger.error(f"Failed to load user data: {e}")
            return {}

    def _get_browser_session_id(self) -> str:
        """Get browser session ID."""
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx

            ctx = get_script_run_ctx()
            if ctx and hasattr(ctx, "session_id"):
                return ctx.session_id
        except Exception:
            pass
        return st.session_state.get("browser_session_id", "unknown")

    def get_session_timeline(self) -> dict[str, Any]:
        """Get formatted session timeline data."""
        timeline = {}

        if self.session_info.get("authenticated", False):
            # Login time
            if self.session_info.get("login_time"):
                login_time = self.session_info["login_time"]
                if isinstance(login_time, str):
                    login_time = datetime.fromisoformat(login_time)
                timeline["login_time"] = login_time.strftime("%H:%M:%S")

            # Session expiry
            if self.user_data.get("session_expires"):
                try:
                    expires = datetime.fromisoformat(self.user_data["session_expires"])
                    remaining = expires - datetime.now()
                    hours = remaining.seconds // 3600
                    minutes = (remaining.seconds % 3600) // 60
                    timeline["expires_in"] = f"{hours}h {minutes}m"
                except ValueError:
                    timeline["expires_in"] = "Invalid format"

            # Session status
            timeline["status"] = (
                "Restored"
                if self.session_info.get("session_restored", False)
                else "Active"
            )

        return timeline


class ContextDebugData:
    """Browser dan environment context information."""

    def __init__(self) -> None:
        self.context_data = self._collect_context_data()

    def _collect_context_data(self) -> dict[str, Any]:
        """Collect all context information."""
        return {
            "network": self._get_network_info(),
            "localization": self._get_localization_info(),
            "cookies": self._get_cookies_info(),
        }

    def _get_network_info(self) -> dict[str, str]:
        """Get network related information."""
        return {
            "url": str(st.context.url),
            "ip_address": st.context.ip_address or "localhost (development)",
            "user_agent": self._format_user_agent(),
        }

    def _format_user_agent(self) -> str:
        """Format user agent for display."""
        user_agent = st.context.headers.get("user-agent", "Not available")
        if user_agent == "Not available":
            return user_agent

        return (
            user_agent.split(")")[0] + ")"
            if ") " in user_agent
            else user_agent[:50] + "..."
        )

    def _get_localization_info(self) -> dict[str, str]:
        """Get localization information."""
        locale_info = {
            "browser_locale": st.context.locale or "Not available",
            "timezone": st.context.timezone or "Not available",
        }

        # Calculate local time if pytz available
        if UTC and st.context.timezone:
            try:
                tz = UTC
                utc_now = datetime.now(UTC)
                local_time = utc_now.astimezone(tz)
                locale_info["local_time"] = local_time.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                locale_info["local_time"] = f"Unable to calculate ({str(e)})"
        else:
            locale_info["local_time"] = "pytz not available"

        return locale_info

    def _get_cookies_info(self) -> list[dict[str, str]]:
        """Get cookies information with categorization."""
        if not st.context.cookies:
            return []

        cookies_list = []
        for name, value in st.context.cookies.items():
            display_value = value[:50] + "..." if len(value) > 50 else value

            cookie_info = {
                "name": name,
                "value": display_value,
                "category": self._categorize_cookie(name),
                "description": self._get_cookie_description(name),
            }
            cookies_list.append(cookie_info)

        return cookies_list

    def _categorize_cookie(self, name: str) -> str:
        """Categorize cookie by name pattern."""
        if name == "ajs_anonymous_id":
            return "Analytics"
        elif name.startswith("Hm_"):
            return "Baidu Analytics"
        elif name == "_streamlit_xsrf":
            return "Security"
        else:
            return "Other"

    def _get_cookie_description(self, name: str) -> str:
        """Get cookie description."""
        descriptions = {
            "ajs_anonymous_id": "🔍 Segment.io analytics tracking",
            "_streamlit_xsrf": "🔒 CSRF protection token",
        }

        if name.startswith("Hm_"):
            return "🔍 Baidu Analytics service"

        return descriptions.get(name, "")


class DatabaseDebugData:
    """Database debug information."""

    def __init__(self) -> None:
        self.db_manager = self._get_db_manager_safely()
        self.db_info = self._get_database_info()

    def _get_db_manager_safely(self) -> DatabaseManager | None:
        """Get database manager with error handling."""
        try:
            return get_database_manager()
        except Exception:
            return None

    def _get_database_info(self) -> dict[str, Any]:
        """Get database information with fallback."""
        if self.db_manager is None:
            return {
                "status": "unavailable",
                "error": "Database manager not initialized",
            }

        try:
            return self.db_manager.get_database_info()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @property
    def connection_status(self) -> dict[str, Any]:
        """Get database connection status."""
        if self.db_manager is None:
            return {"connected": False, "reason": "Manager not available"}

        try:
            # Test connection
            test_query = "SELECT 1 as test"
            result = self.db_manager.query(test_query, ttl=0)

            return {
                "connected": True,
                "test_result": result.iloc[0]["test"] if not result.empty else None,
                "connection_name": self.db_info.get("connection_name", "unknown"),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    @property
    def schema_status(self) -> dict[str, Any]:
        """Get database schema status."""
        if not self.connection_status.get("connected", False):
            return {"valid": False, "reason": "No connection"}

        try:
            tables_info = {}

            # Get tables list
            if "tables" in self.db_info:
                table_names = (
                    self.db_info["tables"].split(",") if self.db_info["tables"] else []
                )

                for table in table_names:
                    count_key = f"{table}_count"
                    if count_key in self.db_info:
                        tables_info[table] = {
                            "exists": True,
                            "row_count": self.db_info[count_key],
                        }

            return {
                "valid": True,
                "table_count": len(tables_info),
                "tables": tables_info,
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}


class LoggingDebugData:
    """Logging system debug information."""

    def __init__(self) -> None:
        self.logging_status = get_logging_status()
        self.state_info = self._get_state_info()

    def _get_state_info(self) -> dict[str, Any]:
        """Get detailed logging state information."""
        return {
            "development_configured": LoggingState.is_dev_configured(),
            "audit_configured": LoggingState.is_audit_configured(),
            "fully_configured": LoggingState.is_fully_configured(),
            "errors": LoggingState.get_errors(),
            "error_count": len(LoggingState.get_errors()),
        }

    @property
    def log_files_status(self) -> dict[str, Any]:
        """Check log files status."""
        log_files = {
            "app.log": Path("logs/app.log"),
            "error.log": Path("logs/error.log"),
            "audit.sqlite": Path("logs/audit.sqlite"),
        }

        status = {}
        for name, path in log_files.items():
            status[name] = {
                "exists": path.exists(),
                "size": path.stat().st_size if path.exists() else 0,
                "path": str(path.resolve()),
            }

        return status


class AppStateDebugData:
    """Enhanced app state debug data."""

    def __init__(self) -> None:
        # Original session state info
        self.session_state_info = self._get_session_state_info()
        self.metrics = self._get_metrics()

        # New database and logging info
        self.database_debug = DatabaseDebugData()
        self.logging_debug = LoggingDebugData()

    def _get_session_state_info(self) -> dict[str, Any]:
        """Get session state information."""
        return {
            "total_keys": len(st.session_state.keys()),
            "keys": list(st.session_state.keys()),
            "query_params": dict(st.query_params)
            if hasattr(st, "query_params")
            else {},
        }

    def _get_metrics(self) -> dict[str, Any]:
        """Get application metrics."""
        if "debug_page_visits" not in st.session_state:
            st.session_state.debug_page_visits = 0
        st.session_state.debug_page_visits += 1

        metrics = {
            "debug_page_visits": st.session_state.debug_page_visits,
            "app_initialized": st.session_state.get("app_initialized", False),
            "streamlit_session_id": st.session_state.get("session_id", "unknown"),
        }

        if "app_start_time" in st.session_state:
            start_time = st.session_state.app_start_time
            uptime = datetime.now() - start_time
            metrics["app_uptime"] = str(uptime).split(".")[0]  # Remove microseconds

        return metrics

    def get_complete_session_state(self) -> dict[str, Any]:
        """Get complete session state for debugging."""
        state = {}
        for key in st.session_state.keys():
            try:
                # Try to serialize the value
                value = st.session_state[key]
                json.dumps(value, default=str)  # Test serialization
                state[key] = value
            except (TypeError, ValueError):
                # If not serializable, convert to string
                state[key] = f"<{type(value).__name__}: {str(value)[:100]}>"
        return state


# Enhanced Debug Report Generator
class DebugReportGenerator:
    """Generate comprehensive debug reports."""

    def __init__(self) -> None:
        self.session_debug = SessionDebugData()
        self.context_debug = ContextDebugData()
        self.app_state_debug = AppStateDebugData()

    def generate_report(self) -> dict[str, Any]:
        """Generate complete debug report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "session": {
                "session_info": self.session_debug.session_info,
                "user_data": self.session_debug.user_data,
                "browser_session_id": self.session_debug.browser_session_id,
            },
            "context": self.context_debug.context_data,
            "app_state": {
                "session_info": self.app_state_debug.session_state_info,
                "metrics": self.app_state_debug.metrics,
            },
            "database": {
                "connection_status": self.app_state_debug.database_debug.connection_status,
                "schema_status": self.app_state_debug.database_debug.schema_status,
                "db_info": self.app_state_debug.database_debug.db_info,
            },
            "logging": {
                "status": self.app_state_debug.logging_debug.logging_status,
                "state": self.app_state_debug.logging_debug.state_info,
                "log_files": self.app_state_debug.logging_debug.log_files_status,
            },
        }

    def export_as_json(self) -> str:
        """Export debug report as JSON string."""
        report = self.generate_report()
        return json.dumps(report, indent=2, default=str)

    def get_filename(self) -> str:
        """Get filename for debug report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"debug_report_{timestamp}.json"


class DebugActionService:
    """Service untuk debug actions dan operations."""

    @staticmethod
    def clear_session_state(keep_keys: list[str] | None = None) -> int:
        """Clear session state, keeping specified keys."""
        if keep_keys is None:
            keep_keys = [
                "page_config_initialized",
                "app_state_initialized",
                "app_start_time",
                "app_initialized",
            ]

        keys_to_remove = [
            key for key in st.session_state.keys() if key not in keep_keys
        ]
        for key in keys_to_remove:
            del st.session_state[key]

        return len(keys_to_remove)

    @staticmethod
    def clear_authentication() -> int:
        """Clear authentication related session state."""
        auth_keys = ["authenticated", "username", "login_time", "session_restored"]
        removed_count = 0

        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]
                removed_count += 1

        return removed_count

    @staticmethod
    def reset_user_data() -> bool:
        """Reset user data file."""
        user_file = Path("user_info.json")
        if user_file.exists():
            user_file.unlink()
            return True
        return False

    @staticmethod
    def force_session_restore() -> bool:
        """Force trigger session restoration."""
        if "authenticated" in st.session_state:
            del st.session_state["authenticated"]
            return True
        return False
