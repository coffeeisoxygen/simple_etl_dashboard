"""User data management dengan clean OOP approach."""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger


class UserData:
    """Data class untuk user information."""

    def __init__(
        self,
        username: str,
        password_hash: str,
        last_login: str | None = None,
        session_active: bool = False,
        session_expires: str | None = None,
        browser_session_id: str | None = None,
        app_session_id: str | None = None,
    ) -> None:
        self.username = username
        self.password_hash = password_hash
        self.last_login = last_login
        self.session_active = session_active
        self.session_expires = session_expires
        self.browser_session_id = browser_session_id
        self.app_session_id = app_session_id

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "last_login": self.last_login,
            "session_active": self.session_active,
            "session_expires": self.session_expires,
            "browser_session_id": self.browser_session_id,
            "app_session_id": self.app_session_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserData":
        """Create UserData from dictionary."""
        return cls(
            username=data.get("username", ""),
            password_hash=data.get("password_hash", ""),
            last_login=data.get("last_login"),
            session_active=data.get("session_active", False),
            session_expires=data.get("session_expires"),
            browser_session_id=data.get("browser_session_id"),
            app_session_id=data.get("app_session_id"),
        )

    def is_session_expired(self) -> bool:
        """Check if session is expired."""
        if not self.session_expires:
            return True

        try:
            expires = datetime.fromisoformat(self.session_expires)
            return datetime.now() > expires
        except ValueError:
            logger.error("Invalid session expiry format")
            return True


class UserManager:
    """Manages user data persistence dan operations."""

    def __init__(self, data_file: Path, session_duration_hours: int = 24) -> None:
        self.data_file = data_file
        self.session_duration_hours = session_duration_hours

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _create_default_user(self) -> UserData:
        """Create default admin user."""
        return UserData(
            username="admin",
            password_hash=self._hash_password("admin123"),
        )

    def load_user_data(self) -> UserData:
        """Load user data from file."""
        if not self.data_file.exists():
            logger.info("Creating default user data file")
            default_user = self._create_default_user()
            self.save_user_data(default_user)
            return default_user

        try:
            with open(self.data_file) as f:
                data = json.load(f)
            return UserData.from_dict(data)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to load user data: {e}")
            logger.info("Creating new default user data")
            return self._create_default_user()

    def save_user_data(self, user_data: UserData) -> None:
        """Save user data to file."""
        try:
            with open(self.data_file, "w") as f:
                json.dump(user_data.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save user data: {e}")

    def verify_password(self, username: str, password: str) -> bool:
        """Verify user credentials."""
        user_data = self.load_user_data()
        return (
            username == user_data.username
            and self._hash_password(password) == user_data.password_hash
        )

    def update_session(
        self,
        browser_session_id: str,
        app_session_id: str,
        active: bool = True,
    ) -> None:
        """Update session information."""
        user_data = self.load_user_data()
        user_data.last_login = datetime.now().isoformat()
        user_data.session_active = active
        user_data.browser_session_id = browser_session_id
        user_data.app_session_id = app_session_id

        if active:
            user_data.session_expires = (
                datetime.now() + timedelta(hours=self.session_duration_hours)
            ).isoformat()
        else:
            user_data.session_expires = None

        self.save_user_data(user_data)

    def clear_session(self) -> None:
        """Clear session data."""
        user_data = self.load_user_data()
        user_data.session_active = False
        user_data.session_expires = None
        user_data.browser_session_id = None
        user_data.app_session_id = None
        self.save_user_data(user_data)

    def change_password(self, old_password: str, new_password: str) -> tuple[bool, str]:
        """Change user password."""
        user_data = self.load_user_data()

        if self._hash_password(old_password) != user_data.password_hash:
            return False, "Password lama salah"

        user_data.password_hash = self._hash_password(new_password)
        self.save_user_data(user_data)

        logger.info("Password changed successfully")
        return True, "Password berhasil diubah"
