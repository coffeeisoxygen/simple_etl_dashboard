"""Debug data collection service dengan clean separation."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import streamlit as st
from loguru import logger
from src.authentication import get_session_info

try:
    import pytz
except ImportError:
    pytz = None


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
        if pytz and st.context.timezone:
            try:
                tz = pytz.timezone(st.context.timezone)
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


class AppStateDebugData:
    """Application state dan metrics information."""

    def __init__(self) -> None:
        self._increment_visit_counter()
        self.metrics = self._collect_metrics()
        self.session_state_info = self._get_session_state_info()

    def _increment_visit_counter(self) -> None:
        """Increment debug page visit counter."""
        if "debug_page_visits" not in st.session_state:
            st.session_state.debug_page_visits = 0
        st.session_state.debug_page_visits += 1

    def _collect_metrics(self) -> dict[str, Any]:
        """Collect application metrics."""
        metrics = {
            "debug_page_visits": st.session_state.debug_page_visits,
            "app_initialized": st.session_state.get("app_initialized", False),
            "streamlit_session_id": self._get_streamlit_session_id(),
        }

        # App uptime calculation
        if "app_start_time" in st.session_state:
            duration = datetime.now() - st.session_state.app_start_time
            metrics["app_uptime"] = (
                f"{duration.seconds // 60}m {duration.seconds % 60}s"
            )

        return metrics

    def _get_streamlit_session_id(self) -> str:
        """Get Streamlit session ID."""
        try:
            from streamlit.runtime.scriptrunner import get_script_run_ctx

            ctx = get_script_run_ctx()
            return ctx.session_id if ctx else "Unable to retrieve"
        except Exception as e:
            return f"Unable to retrieve ({str(e)})"

    def _get_session_state_info(self) -> dict[str, Any]:
        """Get session state information."""
        return {
            "query_params": dict(st.query_params) if st.query_params else {},
            "total_keys": len(st.session_state.keys()),
            "keys_list": list(st.session_state.keys()),
        }

    def get_complete_session_state(self) -> dict[str, str]:
        """Get complete session state as strings."""
        session_dict = {}
        for key in st.session_state.keys():
            try:
                session_dict[key] = str(st.session_state[key])
            except (TypeError, ValueError, AttributeError) as e:
                session_dict[key] = (
                    f"<{type(st.session_state[key]).__name__}: {str(e)}>"
                )

        return session_dict


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


class DebugReportGenerator:
    """Generate comprehensive debug reports."""

    def __init__(self) -> None:
        self.session_data = SessionDebugData()
        self.context_data = ContextDebugData()
        self.app_state_data = AppStateDebugData()

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive debug report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "session_info": self.session_data.session_info,
            "user_data": self.session_data.user_data,
            "context": self.context_data.context_data,
            "app_state": {
                "metrics": self.app_state_data.metrics,
                "session_state_info": self.app_state_data.session_state_info,
            },
        }

    def export_as_json(self) -> str:
        """Export report as JSON string."""
        return json.dumps(self.generate_report(), indent=2)

    def get_filename(self) -> str:
        """Get formatted filename for export."""
        return f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
