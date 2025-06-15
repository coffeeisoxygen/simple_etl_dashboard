"""Database-specific exceptions."""


class DatabaseError(Exception):
    """Base exception for database operations."""

    pass


class ConnectionError(DatabaseError):
    """Database connection failed."""

    pass


class SchemaError(DatabaseError):
    """Database schema operation failed."""

    pass


class QueryError(DatabaseError):
    """Database query execution failed."""

    pass
