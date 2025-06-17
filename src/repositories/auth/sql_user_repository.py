"""SQL User Repository implementation for authentication operations."""

from loguru import logger
from sqlalchemy import select

from db.database import get_session
from models.user_model import User
from protocols.auth.user_repository import IUserRepository


class SQLUserRepository(IUserRepository):
    """SQLAlchemy implementation of IUserRepository for user authentication."""

    def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        try:
            with get_session() as session:
                stmt = select(User).where(User.username == username)
                user = session.scalar(stmt)
                # NOTE: No need to expunge with context manager
                return user
        except Exception as e:
            logger.error(f"Failed to get user by username '{username}': {e}")
            return None

    def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        try:
            with get_session() as session:
                user = session.get(User, user_id)
                return user
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None

    def add_user(self, user: User) -> None:
        """Add new user to database."""
        try:
            with get_session() as session:
                session.add(user)
                session.commit()
                logger.debug(f"User '{user.username}' added successfully")
        except Exception as e:
            logger.error(f"Failed to add user '{user.username}': {e}")
            raise ValueError("Gagal membuat user") from e

    def update(self, user: User) -> None:
        """Update existing user."""
        try:
            with get_session() as session:
                session.merge(user)
                session.commit()
                logger.debug(f"User '{user.username}' updated successfully")
        except Exception as e:
            logger.error(f"Failed to update user '{user.username}': {e}")
            raise ValueError("Gagal memperbarui user") from e
