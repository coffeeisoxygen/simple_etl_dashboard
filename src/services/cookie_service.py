"""Clean cookie service using streamlit-cookies-controller for session persistence."""

import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

import streamlit as st
from loguru import logger
from streamlit_cookies_controller import CookieController


class CookieService:
    """Clean CookieService for session persistence with Streamlit."""

    COOKIE_PREFIX = "etl"
    COOKIE_NAMES = {
        "auth_token": "auth_token",
        "user_data": "user_data",
        "session_uuid": "session_uuid",
    }

    SESSION_KEYS = {
        "auth_token": "cookie_auth_token",
        "user_data": "cookie_user_data",
        "session_uuid": "cookie_session_uuid",
    }

    def __init__(self, expiry_days: int = 7):
        """Initialize cookie service with expiry configuration.

        Args:
            expiry_days: Number of days before cookies expire (default: 7)
        """
        self.expiry_days = expiry_days
        self.controller = CookieController()

    # === Public API ===

    def save(self, user_data: dict[str, Any]) -> str:
        """Save user session to cookies and session state.

        Args:
            user_data: User session data to persist

        Returns:
            str: Generated session UUID for tracking
        """
        session_uuid = str(uuid.uuid4())
        session_data = {
            **user_data,
            "session_uuid": session_uuid,
            "created_at": datetime.now().isoformat(),
            "expires_at": (
                datetime.now() + timedelta(days=self.expiry_days)
            ).isoformat(),
        }

        # Save to cookies for persistence across browser refresh
        self._set_cookie("auth_token", session_uuid)
        self._set_cookie("user_data", json.dumps(session_data))
        self._set_cookie("session_uuid", session_uuid)

        # Cache in session state for immediate access
        self._cache_session(session_data)

        logger.debug(f"Session saved: {session_uuid[:8]}...")
        return session_uuid

    def restore(self) -> dict[str, Any] | None:
        """Restore session from session_state or cookies.

        Returns:
            dict[str, Any] | None: Restored session data if valid, None otherwise
        """
        # Try session state first (fastest access)
        if data := self._from_session_state():
            return data

        # Try cookies with delay for controller readiness
        time.sleep(0.2)
        token = self._get_cookie("auth_token")
        data_json = self._get_cookie("user_data")

        if not token or not data_json:
            return None

        try:
            data = json.loads(data_json)

            # Validate session UUID consistency
            if data.get("session_uuid") != token:
                logger.warning("UUID mismatch between cookies")
                self.clear()
                return None

            # Check expiration
            if self._is_expired(data.get("expires_at")):
                logger.info("Session expired in cookie")
                self.clear()
                return None

            # Cache for performance
            self._cache_session(data)
            return data

        except Exception as e:
            logger.warning(f"Failed to restore cookie session: {e}")
            self.clear()
            return None

    def clear(self) -> None:
        """Clear all session data from cookies and session state."""
        # Clear cookies (silent failures for cleanup)
        for name in self.COOKIE_NAMES.values():
            try:
                self.controller.remove(self._full_cookie_name(name))
            except Exception:
                pass  # Silent failure is OK for cleanup

        # Clear session state
        for key in self.SESSION_KEYS.values():
            st.session_state.pop(key, None)

        logger.debug("Session cleared")

    def has_session(self) -> bool:
        """Check if there's a valid session.

        Returns:
            bool: True if valid session exists
        """
        return self.restore() is not None

    def get_uuid(self) -> str | None:
        """Return session UUID if exists.

        Returns:
            str | None: Current session UUID or None
        """
        return st.session_state.get(
            self.SESSION_KEYS["session_uuid"]
        ) or self._get_cookie("session_uuid")

    def get_info(self) -> dict[str, Any]:
        """Get comprehensive session information for debugging.

        Returns:
            dict[str, Any]: Session status and debug information
        """
        session_uuid = self.get_uuid()

        # Count session state items
        session_count = sum(
            1 for key in self.SESSION_KEYS.values() if key in st.session_state
        )

        # Try to get cookie count (with error handling)
        cookie_count = 0
        try:
            all_cookies = self.controller.getAll() or {}
            cookie_count = sum(
                1
                for name in self.COOKIE_NAMES.values()
                if self._full_cookie_name(name) in all_cookies
            )
        except Exception:
            pass  # Cookie controller might not be ready

        return {
            "has_session": self.has_session(),
            "session_uuid": session_uuid[:8] + "..." if session_uuid else None,
            "expiry_days": self.expiry_days,
            "storage_info": {
                "session_state_items": session_count,
                "browser_cookies": cookie_count,
            },
            "implementation": "streamlit-cookies-controller",
        }

    # === Internal Helpers ===

    def _full_cookie_name(self, name: str) -> str:
        """Generate full cookie name with prefix.

        Args:
            name: Short cookie name

        Returns:
            str: Full cookie name with prefix
        """
        return f"{self.COOKIE_PREFIX}_{name}"

    def _set_cookie(self, name: str, value: str) -> None:
        """Set cookie with error handling.

        Args:
            name: Cookie name (without prefix)
            value: Cookie value
        """
        try:
            self.controller.set(
                self._full_cookie_name(name),
                value,
                max_age=self.expiry_days * 86400,  # Convert days to seconds
            )
        except Exception as e:
            logger.warning(f"Failed to set cookie {name}: {e}")

    def _get_cookie(self, name: str) -> str | None:
        """Get cookie value with error handling.

        Args:
            name: Cookie name (without prefix)

        Returns:
            str | None: Cookie value or None if not found/error
        """
        try:
            return self.controller.get(self._full_cookie_name(name))
        except Exception:
            return None

    def _cache_session(self, data: dict[str, Any]) -> None:
        """Cache session data in Streamlit session state.

        Args:
            data: Session data to cache
        """
        st.session_state[self.SESSION_KEYS["auth_token"]] = data.get("session_uuid")
        st.session_state[self.SESSION_KEYS["user_data"]] = json.dumps(data)
        st.session_state[self.SESSION_KEYS["session_uuid"]] = data.get("session_uuid")

    def _from_session_state(self) -> dict[str, Any] | None:
        """Try to restore session from Streamlit session state.

        Returns:
            dict[str, Any] | None: Session data if valid, None otherwise
        """
        data_json = st.session_state.get(self.SESSION_KEYS["user_data"])
        if not data_json:
            return None

        try:
            data = json.loads(data_json)
            if self._is_expired(data.get("expires_at")):
                logger.debug("Session expired in session_state")
                return None
            return data
        except Exception:
            return None

    def _is_expired(self, iso_expiry: str | None) -> bool:
        """Check if session has expired.

        Args:
            iso_expiry: ISO format expiry datetime string

        Returns:
            bool: True if expired or invalid format
        """
        if not iso_expiry:
            return True
        try:
            return datetime.now() > datetime.fromisoformat(iso_expiry)
        except ValueError:
            return True  # Invalid format = expired


# TODO: Add session encryption for production use
# PINNED: Monitor streamlit-cookies-controller community issues
# REMINDER: Browser cookies have 4KB limit per cookie
# NOTE: Uses hybrid approach - cookies for persistence + session state for performance
