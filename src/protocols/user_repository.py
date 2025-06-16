"""Interface for user repository operations."""

from typing import Protocol

from models.user_model import User


class IUserRepository(Protocol):
    """User repository interface for authentication operations."""

    def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        ...

    def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        ...

    def add_user(self, user: User) -> None:
        """Add new user."""
        ...

    def update(self, user: User) -> None:
        """Update existing user."""
        ...
