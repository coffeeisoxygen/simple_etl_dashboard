"""Authentication manager for orchestrating login/logout with session persistence.

Coordinates between auth_service, user_state, and cookie_service to provide
seamless authentication experience with browser persistence using clean APIs.
"""

from datetime import datetime, timedelta
from typing import Any

from loguru import logger

from repositories.auth.sql_user_repository import SQLUserRepository
from schemas.auth.request import LoginRequest
from schemas.auth.response import LoginResponse
from services.auth_service import login as auth_login
from services.cookie_service import CookieService
from services.user_state import UserState


class AuthManager:
    """Manages authentication flow with session persistence."""

    def __init__(
        self,
        cookie_service: CookieService | None = None,
        session_timeout_minutes: int = 60,
        warning_threshold_minutes: int = 10,
    ):
        """Initialize auth manager with required services and timeout configuration."""
        self.user_state = UserState()
        self.cookie_service = cookie_service or CookieService()
        self.user_repository = SQLUserRepository()
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.warning_threshold = timedelta(minutes=warning_threshold_minutes)

    def is_authenticated(self) -> bool:
        """Check if user is authenticated with auto-restore from cookies and timeout validation."""
        if self.user_state.is_authenticated():
            if self._is_session_expired():
                logger.warning("Session expired, logging out user")
                self.logout_with_cleanup()
                return False
            return True
        return self._try_restore()

    def login_with_persistence(self, login_request: LoginRequest) -> LoginResponse:
        """Authenticate user and persist session to cookies."""
        try:
            user = auth_login(login_request, self.user_repository)
            self.user_state.login_user(user)

            # ✅ FIX: Proper field mapping for cookies
            session_data = self._prepare_session_data(user)
            session_uuid = self.cookie_service.save(session_data)

            logger.info(
                f"Login success: {user.username} (Session: {session_uuid[:8]}...)"
            )
            return user

        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    def logout_with_cleanup(self) -> None:
        """Logout user and clean up all session data."""
        username = self.user_state.get_username()
        session_uuid = self.cookie_service.get_uuid()

        self.user_state.logout_user()
        self.cookie_service.clear()

        logger.info(
            f"Logout success: {username or 'unknown'} "
            f"(Session: {session_uuid[:8] if session_uuid else 'n/a'}...)"
        )

    def get_current_user(self) -> LoginResponse | None:
        """Get current authenticated user data."""
        if not self.is_authenticated():
            return None

        try:
            # ✅ FIX: Add null checks before LoginResponse construction
            user_id = self.user_state.get_user_id()
            username = self.user_state.get_username()
            user_name = self.user_state.get_user_name()

            # Return None if any required field is missing
            if user_id is None or username is None or user_name is None:
                logger.warning(
                    "Incomplete user data in state, cannot create LoginResponse"
                )
                return None

            return LoginResponse(
                id=user_id,
                username=username,
                name=user_name,
                is_admin=self.user_state.is_admin(),
                is_active=self.user_state.is_active(),
            )
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            return None

    def require_authentication(self) -> None:
        """Guard method to ensure user is authenticated."""
        if not self.is_authenticated():
            self.user_state.require_auth()

    def require_admin_access(self) -> None:
        """Guard method to ensure user has admin privileges."""
        self.require_authentication()
        self.user_state.require_admin()

    def get_session_timeout_info(self) -> dict[str, Any] | None:
        """Get session timeout information including warnings."""
        if not self.user_state.is_authenticated():
            return None

        login_time = self.user_state.get_login_timestamp()
        if not login_time:
            return None

        current_time = datetime.now()
        session_age = current_time - login_time
        time_remaining = self.session_timeout - session_age

        is_expired = time_remaining.total_seconds() <= 0
        needs_warning = time_remaining <= self.warning_threshold and not is_expired

        return {
            "session_age_minutes": int(session_age.total_seconds() / 60),
            "time_remaining_minutes": max(0, int(time_remaining.total_seconds() / 60)),
            "is_expired": is_expired,
            "needs_warning": needs_warning,
            "warning_message": self._get_timeout_warning_message(time_remaining)
            if needs_warning
            else None,
        }

    def check_session_timeout_warning(self) -> str | None:
        """Check if session needs timeout warning and return warning message."""
        timeout_info = self.get_session_timeout_info()
        if not timeout_info:
            return None

        if timeout_info["is_expired"]:
            logger.warning("Session has expired")
            self.logout_with_cleanup()
            return "Your session has expired. Please log in again."

        if timeout_info["needs_warning"]:
            warning_msg = timeout_info["warning_message"]
            logger.info(f"Session timeout warning: {warning_msg}")
            return warning_msg

        return None

    def extend_session(self) -> bool:
        """Extend current session by updating login timestamp."""
        if not self.user_state.is_authenticated():
            return False

        try:
            # Update login timestamp in user state
            current_user = self.get_current_user()
            if current_user:
                self.user_state.login_user(current_user)

                # Update cookie with new timestamp
                session_data = self._prepare_session_data(current_user)
                self.cookie_service.save(session_data)

                logger.info(f"Session extended for user: {current_user.username}")
                return True
        except Exception as e:
            logger.error(f"Failed to extend session: {e}")

        return False

    def get_session_info(self) -> dict[str, Any]:
        """Get comprehensive session information for debugging."""
        current_user = self.get_current_user()
        timeout_info = self.get_session_timeout_info()

        return {
            "is_authenticated": self.is_authenticated(),
            "current_user": current_user.__dict__ if current_user else None,
            "cookie_info": self.cookie_service.get_info(),
            "user_state_info": {
                "user_id": self.user_state.get_user_id(),
                "username": self.user_state.get_username(),
                "user_name": self.user_state.get_user_name(),
                "is_admin": self.user_state.is_admin(),
                "is_active": self.user_state.is_active(),
                "login_timestamp": self.user_state.get_login_timestamp(),
            },
            "timeout_info": timeout_info,
        }

    # === Internal Helper Methods ===

    def _try_restore(self) -> bool:
        """Attempt to restore user session from browser cookies."""
        try:
            data = self.cookie_service.restore()
            if not self._is_valid(data):
                self.cookie_service.clear()
                return False

            # ✅ FIX: Explicit null check for type safety
            if data is None:
                return False

            # ✅ FIX: Map cookie field names back to LoginResponse field names
            user_data = self._prepare_user_data(data)
            user = LoginResponse(**user_data)

            self.user_state.login_user(user)
            logger.info(f"Session restored from cookie: {user.username}")
            return True

        except Exception as e:
            logger.warning(f"Restore failed: {e}")
            self.cookie_service.clear()
            return False

    def _is_valid(self, data: Any) -> bool:
        """Validate session data has required fields with correct types."""
        if not data:
            return False

        required = {
            "user_id": int,
            "username": str,
            "user_name": str,  # Note: cookies use user_name, LoginResponse uses name
            "is_admin": bool,
            "is_active": bool,
        }

        # ✅ FIX: Proper validation for boolean values
        return all(k in data and isinstance(data[k], t) for k, t in required.items())

    def _prepare_session_data(self, user: LoginResponse) -> dict[str, Any]:
        """Prepare user data for cookie storage."""
        data = user.model_dump()
        # ✅ Map LoginResponse fields to cookie field names
        data["user_id"] = data.pop("id")  # id -> user_id
        data["user_name"] = data.pop("name")  # name -> user_name
        return data

    def _prepare_user_data(self, cookie_data: dict[str, Any]) -> dict[str, Any]:
        """Prepare cookie data for LoginResponse constructor."""
        data = cookie_data.copy()
        # ✅ Map cookie field names back to LoginResponse fields
        data["id"] = data.pop("user_id")  # user_id -> id
        data["name"] = data.pop("user_name")  # user_name -> name
        return data

    def _is_session_expired(self) -> bool:
        """Check if current session has expired."""
        login_time = self.user_state.get_login_timestamp()
        if not login_time:
            return True

        current_time = datetime.now()
        session_age = current_time - login_time
        return session_age >= self.session_timeout

    def _get_timeout_warning_message(self, time_remaining: timedelta) -> str:
        """Generate appropriate timeout warning message."""
        minutes_remaining = int(time_remaining.total_seconds() / 60)

        if minutes_remaining <= 1:
            return (
                "Your session will expire in less than 1 minute. Please save your work."
            )
        elif minutes_remaining <= 5:
            return f"Your session will expire in {minutes_remaining} minutes. Please save your work."
        else:
            return f"Your session will expire in {minutes_remaining} minutes."


# === Global Instance Management ===

_auth_manager: AuthManager | None = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
        logger.debug("Created global auth manager instance")
    return _auth_manager


def reset_auth_manager() -> None:
    """Reset global auth manager instance (useful for testing)."""
    global _auth_manager
    _auth_manager = None
    logger.debug("Reset global auth manager")


# COMPLETED: Add session timeout warnings - implemented with configurable timeouts and warning messages
# PINNED: Consider adding refresh token mechanism
# REMINDER: AuthManager coordinates between services, doesn't implement auth logic
# NOTE: Uses dependency injection for better testability
