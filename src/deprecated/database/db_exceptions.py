"""Database exception classes for enhanced error handling."""


class DatabaseError(Exception):
    """Base exception for database operations."""

    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails."""

    pass


class QueryError(DatabaseError):
    """Exception raised when database query fails."""

    pass


class SchemaError(DatabaseError):
    """Exception raised when database schema operations fail."""

    pass


class ValidationError(DatabaseError):
    """Exception raised when data validation fails."""

    pass
