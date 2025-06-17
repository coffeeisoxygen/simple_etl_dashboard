"""Database module for ETL Dashboard.

Complete database functionality including connection management, initialization,
and utility functions. Single source of truth for all database operations.

REMINDER: Uses Streamlit's st.connection() API with secrets.toml configuration
"""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from loguru import logger
from sqlalchemy import Engine, func, select, text
from sqlalchemy.orm import Session

from models.base import Base
from models.user_model import User

# Constants
SQLITE_URL_PREFIX = "sqlite:///"
DEFAULT_QUERY_TTL = 60


class StreamlitSQLManager:
    """Streamlit-compatible SQL database manager.

    Handles connection management, session handling, and basic operations
    using Streamlit's native st.connection API with proper error handling.
    """

    def __init__(self, connection_name: str = "sql") -> None:
        """Initialize SQL manager with connection name.

        Args:
            connection_name: Name of connection in secrets.toml
        """
        self.connection_name = connection_name
        self._ensure_data_directory()
        logger.debug(f"SQL manager initialized for connection: {connection_name}")

    def _ensure_data_directory(self) -> None:
        """Ensure data directory exists - simple and clean.

        SQLite will create the database file automatically,
        we just need to ensure the parent directory exists.
        """
        try:
            # Simple approach: just ensure data directory exists
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            logger.debug(f"Data directory ensured: {data_dir.resolve()}")

        except Exception as e:
            logger.warning(f"Could not create data directory: {e}")
            # NOTE: If this fails, SQLite connection will fail anyway

    def get_connection(self) -> st.connections.SQLConnection:  # type: ignore
        """Get Streamlit SQL connection with error handling.

        Returns:
            Streamlit SQL connection instance

        Raises:
            Exception: If connection cannot be established
        """
        try:
            conn = st.connection(self.connection_name, type="sql")
            logger.debug("SQL connection retrieved successfully")
            return conn
        except Exception as e:
            logger.error(f"Failed to get SQL connection '{self.connection_name}': {e}")
            logger.error(
                f"Available connections: {list(st.secrets.get('connections', {}).keys())}"
            )
            raise

    def get_engine(self) -> Engine:
        """Get SQLAlchemy engine from Streamlit connection.

        Returns:
            SQLAlchemy engine instance
        """
        return self.get_connection().engine

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with proper cleanup.

        Yields:
            SQLAlchemy session instance
        """
        with self.get_connection().session as session:
            try:
                yield session
                logger.debug("Database session completed successfully")
            except Exception as e:
                logger.error(f"Database session error: {e}")
                raise

    def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        ttl: int = DEFAULT_QUERY_TTL,
        **kwargs,
    ) -> pd.DataFrame:
        """Execute SQL query and return DataFrame.

        Args:
            sql: SQL query string
            params: Query parameters
            ttl: Cache time-to-live in seconds
            **kwargs: Additional arguments passed to connection.query

        Returns:
            Query results as DataFrame
        """
        try:
            df = self.get_connection().query(sql, params=params, ttl=ttl, **kwargs)
            logger.debug(f"Query executed successfully, returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Query failed: {e}\nSQL: {sql}\nParams: {params}")
            raise

    def execute_write(self, sql: str, params: dict[str, Any] | None = None) -> None:
        """Execute write operations (INSERT, UPDATE, DELETE).

        Args:
            sql: SQL statement string
            params: Statement parameters
        """
        with self.get_session() as session:
            session.execute(text(sql), params or {})
            session.commit()
            logger.debug(f"Write operation executed: {sql}")

    def health_check(self) -> dict[str, Any]:
        """Check database health and connectivity.

        Returns:
            Dictionary with health status information
        """
        try:
            # Execute simple connectivity test
            self.query("SELECT 1 AS health_check", ttl=0)

            # Get connection info
            conn = self.get_connection()
            db_url = str(conn.engine.url)

            health_info: dict[str, Any] = {
                "status": "healthy",
                "connection": "ok",
                "database_url": db_url,
                "streamlit_connection": True,
            }

            # Add file info for SQLite
            if SQLITE_URL_PREFIX in db_url:
                db_path = Path(db_url.replace(SQLITE_URL_PREFIX, ""))
                file_info: dict[str, Any] = {
                    "file_exists": db_path.exists(),
                    "file_path": str(db_path.resolve()),
                    "file_size_mb": round(db_path.stat().st_size / 1024 / 1024, 2)
                    if db_path.exists()
                    else 0,
                }
                health_info.update(file_info)

            return health_info

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed",
                "streamlit_connection": False,
            }


# =============================================================================
# Global Instance Management
# =============================================================================

_sql_manager: StreamlitSQLManager | None = None


def get_sql_manager() -> StreamlitSQLManager:
    """Get the global SQL manager instance.

    Returns:
        Global SQL manager instance
    """
    global _sql_manager
    if _sql_manager is None:
        _sql_manager = StreamlitSQLManager()
        logger.debug("Created global SQL manager instance")
    return _sql_manager


# =============================================================================
# Database Initialization Functions
# =============================================================================


def initialize_database() -> bool:
    """Initialize database: create tables and seed initial data.

    This is the main entry point for database setup, called during app initialization.
    Combines table creation and data seeding using proper service layers.

    Returns:
        True if initialization successful, False otherwise
    """
    try:
        logger.info("Starting database initialization...")

        # Step 1: Create tables (database layer responsibility)
        if not create_tables():
            logger.error("Table creation failed")
            return False

        # Step 2: Seed data (business layer responsibility)
        from services.seed_service import seed_all

        if not seed_all():
            logger.error("Data seeding failed")
            return False

        logger.success("Database initialization completed successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.exception("Full initialization error traceback:")
        return False


def create_tables() -> bool:
    """Create all database tables from SQLAlchemy models.

    Pure database operation - infrastructure layer responsibility.

    Returns:
        True if tables created successfully, False otherwise
    """
    try:
        logger.info("Creating database tables...")
        engine = get_sql_manager().get_engine()
        Base.metadata.create_all(bind=engine)
        logger.success("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
        return False


def get_database_status() -> dict[str, Any]:
    """Get comprehensive database status information.

    Combines health check with additional database metrics.
    Useful for admin dashboard and monitoring.

    Returns:
        Dictionary with complete database status
    """
    try:
        # Get basic health info
        health_info = get_sql_manager().health_check()

        # Add additional metrics if database is healthy
        if health_info.get("status") == "healthy":
            with get_sql_manager().get_session() as session:
                # Count users
                user_count = session.execute(select(func.count(User.id))).scalar() or 0

                health_info.update(
                    {
                        "user_count": user_count,
                        "tables_created": True,
                        "admin_exists": user_count > 0,
                    }
                )

        return health_info

    except Exception as e:
        logger.error(f"Database status check failed: {e}")
        return {
            "status": "error",
            "error": f"Status check failed: {e}",
            "tables_created": False,
            "admin_exists": False,
        }


# =============================================================================
# Convenience Functions for Common Operations
# =============================================================================


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get database session context manager.

    Yields:
        SQLAlchemy session instance
    """
    with get_sql_manager().get_session() as session:
        yield session


def query_data(
    sql: str,
    params: dict[str, Any] | None = None,
    ttl: int = DEFAULT_QUERY_TTL,
    **kwargs,
) -> pd.DataFrame:
    """Execute SQL query and return DataFrame.

    Args:
        sql: SQL query string
        params: Query parameters
        ttl: Cache time-to-live in seconds
        **kwargs: Additional query arguments

    Returns:
        Query results as DataFrame
    """
    return get_sql_manager().query(sql, params, ttl, **kwargs)


def execute_write(sql: str, params: dict[str, Any] | None = None) -> None:
    """Execute write SQL statement.

    Args:
        sql: SQL statement string
        params: Statement parameters
    """
    get_sql_manager().execute_write(sql, params)


def check_database_health() -> dict[str, Any]:
    """Check database health and connectivity.

    Returns:
        Dictionary with health status information
    """
    return get_sql_manager().health_check()


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Core class
    "StreamlitSQLManager",
    "get_sql_manager",
    # Initialization functions
    "initialize_database",
    "create_tables",
    "get_database_status",
    # Common operations
    "get_session",
    "query_data",
    "execute_write",
    "check_database_health",
]
