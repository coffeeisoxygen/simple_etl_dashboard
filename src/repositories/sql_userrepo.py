"""SQL User Repository implementation for authentication operations."""

from loguru import logger
from sqlalchemy import select

from database import get_db_session
from models.user_model import User
from protocols.user_repository import IUserRepository


class SQLUserRepository(IUserRepository):
    """SQL User Repository for user CRUD operations.

    This repository handles user database operations using the new
    database architecture with clean session management and proper
    object lifecycle handling to prevent DetachedInstanceError.
    """

    def __init__(self) -> None:
        """Initialize repository with cached session manager."""
        self.db = get_db_session()

    def get_by_username(self, username: str) -> User | None:
        """Get user by username - CRUD operation."""
        try:
            with self.db.session_scope() as session:
                stmt = select(User).where(User.username == username)
                user = session.scalar(stmt)
                if user:
                    # Eagerly load all attributes to ensure they're available
                    _ = user.id
                    _ = user.username
                    _ = user.name
                    _ = user.password_hash
                    _ = user.is_admin
                    _ = user.is_active
                    _ = user.tgl_data

                    # ✅ FIX: Detach from session to prevent DetachedInstanceError
                    session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Failed to get user by username '{username}': {e}")
            return None

    def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID - CRUD operation."""
        try:
            with self.db.session_scope() as session:
                user = session.get(User, user_id)
                if user:
                    # Eagerly load all attributes to ensure they're available
                    _ = user.id
                    _ = user.username
                    _ = user.name
                    _ = user.password_hash
                    _ = user.is_admin
                    _ = user.is_active
                    _ = user.tgl_data

                    # ✅ FIX: Detach from session to prevent DetachedInstanceError
                    session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            return None

    def add_user(self, user: User) -> None:
        """Add single user - CRUD operation."""
        try:
            with self.db.session_scope() as session:
                session.add(user)
                # Auto-commit via session_scope
                logger.debug(f"User '{user.username}' added successfully")
        except Exception as e:
            logger.error(f"Failed to add user '{user.username}': {e}")
            raise ValueError(f"Failed to create user: {e}") from e

    def update(self, user: User) -> None:
        """Update user - CRUD operation.

        NOTE: For detached objects, we use merge() to reattach to session.
        """
        try:
            with self.db.session_scope() as session:
                # ✅ FIX: Use merge() for detached objects
                # This handles both attached and detached User objects
                session.merge(user)
                # Auto-commit via session_scope
                logger.debug(f"User '{user.username}' updated successfully")
        except Exception as e:
            logger.error(f"Failed to update user '{user.username}': {e}")
            raise ValueError(f"Failed to update user: {e}") from e
