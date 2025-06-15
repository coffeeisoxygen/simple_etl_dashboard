"""Unified database manager for ETL Dashboard."""

from typing import Any

import pandas as pd
import streamlit as st
from loguru import logger

from src.database.db_config import DatabaseConfig
from src.database.db_schema import DatabaseSchema
from src.database.exceptions import ConnectionError, QueryError, SchemaError


class DatabaseManager:
    """Unified database manager for ETL Dashboard."""

    def __init__(self) -> None:
        self._connection: Any = None
        self._setup_database()

    def _setup_database(self) -> None:
        """Setup database connection and schema."""
        if "database_initialized" in st.session_state:
            return

        try:
            self._test_connection()
            self._create_tables()
            st.session_state.database_initialized = True
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise SchemaError(f"Failed to initialize database: {e}") from e

    def _get_connection(self) -> Any:
        """Get Streamlit SQL connection."""
        if self._connection is None:
            try:
                config = DatabaseConfig.get_connection_config()
                self._connection = st.connection(
                    DatabaseConfig.CONNECTION_NAME, type="sql", **config
                )
            except Exception as e:
                raise ConnectionError(f"Failed to create connection: {e}") from e
        return self._connection

    def _test_connection(self) -> None:
        """Test database connection."""
        try:
            conn = self._get_connection()
            test_df = conn.query("SELECT 1 as test", ttl=DatabaseConfig.NO_CACHE_TTL)

            if test_df.empty or test_df.iloc[0]["test"] != 1:
                raise ConnectionError("Connection test failed - invalid response")

            logger.info(
                f"Database connection established: {DatabaseConfig.get_database_url()}"
            )
        except ConnectionError:
            raise
        except Exception as e:
            logger.error(f"Failed to test database connection: {e}")
            raise ConnectionError(f"Connection test failed: {e}") from e

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            conn = self._get_connection()
            schema_statements = DatabaseSchema.get_create_statements()

            for i, statement in enumerate(schema_statements):
                try:
                    conn.query(statement, ttl=DatabaseConfig.NO_CACHE_TTL)
                except Exception as e:
                    logger.error(
                        f"Failed to execute statement {i + 1}: {statement[:100]}..."
                    )
                    raise SchemaError(
                        f"Schema creation failed at statement {i + 1}: {e}"
                    ) from e

            logger.info("Database schema created/verified successfully")
        except SchemaError:
            raise
        except Exception as e:
            logger.error(f"Failed to create database schema: {e}")
            raise SchemaError(f"Schema setup failed: {e}") from e

    def query(
        self, sql: str, params: dict[str, Any] | None = None, ttl: int | None = None
    ) -> pd.DataFrame:
        """Execute read query with caching."""
        if ttl is None:
            ttl = DatabaseConfig.DEFAULT_TTL

        try:
            conn = self._get_connection()
            return conn.query(sql, params=params, ttl=ttl)
        except Exception as e:
            logger.error(f"Query execution failed: {sql[:100]}... - {e}")
            raise QueryError(f"Query failed: {e}") from e

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
        """Execute write operation."""
        try:
            conn = self._get_connection()
            return conn.query(sql, params=params, ttl=DatabaseConfig.NO_CACHE_TTL)
        except Exception as e:
            logger.error(f"Execute operation failed: {sql[:100]}... - {e}")
            raise QueryError(f"Execute failed: {e}") from e

    def get_database_info(self) -> dict[str, Any]:
        """Get database information for debugging."""
        try:
            return self._gather_database_info()
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}

    def _gather_database_info(self) -> dict[str, Any]:
        """Internal method to gather database information."""
        db_file = DatabaseConfig.DB_FILE

        info = {
            "database_file": str(db_file.resolve()),
            "file_exists": db_file.exists(),
            "file_size": db_file.stat().st_size if db_file.exists() else 0,
            "connection_url": DatabaseConfig.get_database_url(),
            "connection_name": DatabaseConfig.CONNECTION_NAME,
        }

        if db_file.exists():
            info.update(self._get_table_info())

        return info

    def _get_table_info(self) -> dict[str, Any]:
        """Get table information from database."""
        table_info = {}

        try:
            tables_query = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
            tables_df = self.query(tables_query, ttl=60)
            tables_list = tables_df["name"].tolist() if not tables_df.empty else []
            table_info["tables"] = ",".join(tables_list)

            # Get record counts
            for table in tables_list:
                try:
                    count_df = self.query(
                        f"SELECT COUNT(*) as count FROM {table}", ttl=60
                    )
                    table_info[f"{table}_count"] = count_df.iloc[0]["count"]
                except Exception as e:
                    logger.warning(f"Failed to get count for table {table}: {e}")
                    table_info[f"{table}_count"] = "error"

        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            table_info["table_info_error"] = str(e)

        return table_info


@st.cache_resource
def get_database_manager() -> DatabaseManager:
    """Get or create database manager instance."""
    return DatabaseManager()


def init_database() -> DatabaseManager:
    """Initialize database - convenience function."""
    return get_database_manager()
