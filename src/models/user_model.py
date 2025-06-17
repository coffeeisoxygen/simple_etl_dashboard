from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, comment="User primary key"
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username for login",
    )

    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="User display name"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Bcrypt hashed password"
    )

    is_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="Admin privileges flag"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Account active status"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Record creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
        comment="Record last update timestamp",
    )

    def __repr__(self) -> str:
        """String representation for debugging.

        Extended summary can include more details about the object state.

        Returns:
            str: A string representation of the User object.
        """
        return f"<User(id={self.id}, username='{self.username}', name='{self.name}')>"

    def __str__(self) -> str:
        """Human-readable string representation.

        Extended summary can include more details about the object state.

        Returns:
            str: A human-readable string representation of the User object.
        """
        return f"{self.name} ({self.username})"
