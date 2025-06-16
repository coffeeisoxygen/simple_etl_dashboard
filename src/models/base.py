"""Base model and database setup for SQLAlchemy v2."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models.

    Following SQLAlchemy v2 best practices for declarative base.
    All models should inherit from this class.
    """

    pass
