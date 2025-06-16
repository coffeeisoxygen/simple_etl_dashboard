"""User model following SQLAlchemy v2 best practices."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    """User model for application authentication and authorization.

    Following SQLAlchemy v2 declarative style with proper type annotations.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment="User primary key"
    )

    # Required fields
    username: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="Unique username for login"
    )

    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="User display name"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Bcrypt hashed password"
    )

    # Boolean fields with defaults
    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Admin privileges flag"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Account active status"
    )

    # Timestamp - FIXED: Use server_default for proper timestamp
    tgl_data: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),  # ✅ FIXED: Use SQL function, not Python
        nullable=False,
        comment="Record creation timestamp",
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User(id={self.id}, username='{self.username}', name='{self.name}')>"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.name} ({self.username})"
