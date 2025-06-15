"""Enhanced database manager with Monthly Partitioning & Backup Support."""

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pandas as pd
import streamlit as st
from loguru import logger
from sqlalchemy import text
from streamlit.connections import SQLConnection

from src.database.db_config import DatabaseConfig
from src.database.db_exceptions import ConnectionError, QueryError, SchemaError
from src.database.db_schema import DatabaseSchema


class DatabaseManager:
    """Enhanced database manager with monthly partitioning and backup support."""

    def __init__(self) -> None:
        """Initialize database manager with monthly partitioning support."""
        self.config = DatabaseConfig()
        self._master_connection: SQLConnection | None = None
        self._monthly_connections: dict[str, SQLConnection] = {}
        self._setup_databases()

    def _setup_databases(self) -> None:
        """Setup master and monthly databases."""
        try:
            # Ensure directories exist
            self.config.ensure_directories()

            # Setup master database
            self._setup_master_database()

            # Setup current month database
            current_month = self.config.get_current_month_period()
            self._setup_monthly_database(current_month)

            logger.info(
                "Database manager initialized with monthly partitioning support"
            )

        except Exception as e:
            logger.error(f"Database manager initialization failed: {e}")
            raise SchemaError(f"Database setup failed: {e}") from e

    def _setup_master_database(self) -> None:
        """Setup master database."""
        try:
            # Test master connection
            master_conn = self._get_master_connection()
            result = master_conn.query("SELECT 1 as test", ttl=0)

            if result.empty or result.iloc[0]["test"] != 1:
                raise ConnectionError("Master database connection test failed")

            # Create master tables
            self._create_master_tables()
            logger.info("Master database setup completed")

        except Exception as e:
            logger.error(f"Master database setup failed: {e}")
            raise SchemaError(f"Master database setup failed: {e}") from e

    def _setup_monthly_database(self, year_month: str) -> None:
        """Setup monthly database for given period."""
        try:
            # Test monthly connection
            monthly_conn = self._get_monthly_connection(year_month)
            result = monthly_conn.query("SELECT 1 as test", ttl=0)

            if result.empty or result.iloc[0]["test"] != 1:
                raise ConnectionError(
                    f"Monthly database connection test failed: {year_month}"
                )

            # Create monthly tables
            self._create_monthly_tables(year_month)

            # Register monthly database
            self._register_monthly_database(year_month)

            logger.info(f"Monthly database setup completed: {year_month}")

        except Exception as e:
            logger.error(f"Monthly database setup failed for {year_month}: {e}")
            raise SchemaError(f"Monthly database setup failed: {e}") from e

    def _create_master_tables(self) -> None:
        """Create master database tables."""
        try:
            conn = self._get_master_connection()
            statements = DatabaseSchema.get_master_database_tables()
            indexes = DatabaseSchema.get_master_indexes()
            views = DatabaseSchema.get_master_views()

            with conn.session as session:
                session.execute(text("PRAGMA foreign_keys = ON"))

                # Create tables
                for statement in statements:
                    session.execute(text(statement))

                # Create indexes
                for index in indexes:
                    session.execute(text(index))

                # Create views
                for view in views:
                    session.execute(text(view))

                session.commit()

            logger.info(
                f"Master database: {len(statements)} tables, {len(indexes)} indexes, {len(views)} views created"
            )

        except Exception as e:
            logger.error(f"Master table creation failed: {e}")
            raise SchemaError(f"Failed to create master tables: {e}") from e

    def _create_monthly_tables(self, year_month: str) -> None:
        """Create monthly database tables."""
        try:
            conn = self._get_monthly_connection(year_month)
            statements = DatabaseSchema.get_monthly_database_tables()
            indexes = DatabaseSchema.get_monthly_indexes()
            views = DatabaseSchema.get_monthly_views()

            with conn.session as session:
                session.execute(text("PRAGMA foreign_keys = ON"))

                # Create tables
                for statement in statements:
                    session.execute(text(statement))

                # Create indexes
                for index in indexes:
                    session.execute(text(index))

                # Create views
                for view in views:
                    session.execute(text(view))

                session.commit()

            logger.info(
                f"Monthly database {year_month}: {len(statements)} tables, {len(indexes)} indexes, {len(views)} views created"
            )

        except Exception as e:
            logger.error(f"Monthly table creation failed for {year_month}: {e}")
            raise SchemaError(f"Failed to create monthly tables: {e}") from e

    def _register_monthly_database(self, year_month: str) -> None:
        """Register monthly database in master registry."""
        try:
            db_path = self.config.get_monthly_database_path(year_month)
            file_size = self.config.get_database_file_size(db_path)

            # Get territory_id (assuming single territory for now - can be enhanced)
            territory_id = self._get_default_territory_id()

            self.execute_master(
                """
                INSERT OR REPLACE INTO monthly_database_registry
                (month_period, database_file, territory_id, status, file_size, created_date, last_access_date)
                VALUES (:month_period, :database_file, :territory_id, 'ACTIVE', :file_size, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                {
                    "month_period": year_month,
                    "database_file": str(db_path),
                    "territory_id": territory_id,
                    "file_size": file_size,
                },
            )

            logger.info(f"Monthly database registered: {year_month}")

        except Exception as e:
            logger.warning(f"Failed to register monthly database {year_month}: {e}")

    def _get_default_territory_id(self) -> int:
        """Get default territory ID - helper method."""
        try:
            result = self.query_master("SELECT id FROM territory ORDER BY id LIMIT 1")
            return result.iloc[0]["id"] if not result.empty else 1
        except Exception:
            return 1  # Fallback default

    def _get_master_connection(self) -> SQLConnection:
        """Get master database connection."""
        if self._master_connection is None:
            try:
                # Type cast to SQLConnection for proper type hints
                connection = st.connection(
                    self.config.MASTER_CONNECTION_NAME,
                    type="sql",
                    url=self.config.get_master_database_url(),
                    **self.config.get_connection_config(),
                )
                self._master_connection = cast(SQLConnection, connection)

            except Exception as e:
                logger.error(f"Failed to create master connection: {e}")
                raise ConnectionError(f"Master connection failed: {e}") from e

        return self._master_connection

    def _get_monthly_connection(self, year_month: str) -> SQLConnection:
        """Get monthly database connection."""
        if year_month not in self._monthly_connections:
            try:
                connection_name = self.config.get_monthly_connection_name(year_month)

                # Type cast to SQLConnection for proper type hints
                connection = st.connection(
                    connection_name,
                    type="sql",
                    url=self.config.get_monthly_database_url(year_month),
                    **self.config.get_connection_config(),
                )
                self._monthly_connections[year_month] = cast(SQLConnection, connection)

            except Exception as e:
                logger.error(
                    f"Failed to create monthly connection for {year_month}: {e}"
                )
                raise ConnectionError(f"Monthly connection failed: {e}") from e

        return self._monthly_connections[year_month]

    # Master Database Operations
    def query_master(
        self, sql: str, ttl: int = DatabaseConfig.DEFAULT_TTL, **kwargs
    ) -> pd.DataFrame:
        """Execute query on master database."""
        try:
            conn = self._get_master_connection()
            result = conn.query(sql, ttl=ttl, **kwargs)
            logger.debug(f"Master query executed: {len(result)} rows returned")
            return result
        except Exception as e:
            logger.error(f"Master query failed: {sql[:100]}... - {e}")
            raise QueryError(f"Master query failed: {e}") from e

    def execute_master(self, sql: str, params: dict[str, Any] | None = None) -> None:
        """Execute DML on master database."""
        try:
            conn = self._get_master_connection()
            with conn.session as session:
                session.execute(text("PRAGMA foreign_keys = ON"))
                session.execute(text(sql), params or {})
                session.commit()
                logger.debug("Master DML executed successfully")
        except Exception as e:
            logger.error(f"Master DML failed: {sql[:100]}... - {e}")
            raise QueryError(f"Master execute failed: {e}") from e

    # Monthly Database Operations
    def query_monthly(
        self, year_month: str, sql: str, ttl: int = DatabaseConfig.DEFAULT_TTL, **kwargs
    ) -> pd.DataFrame:
        """Execute query on monthly database."""
        try:
            # Ensure monthly database exists
            if year_month not in self.config.list_monthly_databases():
                self._setup_monthly_database(year_month)

            conn = self._get_monthly_connection(year_month)
            result = conn.query(sql, ttl=ttl, **kwargs)

            # Update last access time
            self._update_database_access_time(year_month)

            logger.debug(
                f"Monthly query executed on {year_month}: {len(result)} rows returned"
            )
            return result
        except Exception as e:
            logger.error(f"Monthly query failed on {year_month}: {sql[:100]}... - {e}")
            raise QueryError(f"Monthly query failed: {e}") from e

    def execute_monthly(
        self, year_month: str, sql: str, params: dict[str, Any] | None = None
    ) -> None:
        """Execute DML on monthly database."""
        try:
            # Ensure monthly database exists
            if year_month not in self.config.list_monthly_databases():
                self._setup_monthly_database(year_month)

            conn = self._get_monthly_connection(year_month)
            with conn.session as session:
                session.execute(text("PRAGMA foreign_keys = ON"))
                session.execute(text(sql), params or {})
                session.commit()

            # Update last access time
            self._update_database_access_time(year_month)

            logger.debug(f"Monthly DML executed on {year_month}")
        except Exception as e:
            logger.error(f"Monthly DML failed on {year_month}: {sql[:100]}... - {e}")
            raise QueryError(f"Monthly execute failed: {e}") from e

    def _update_database_access_time(self, year_month: str) -> None:
        """Update last access time for monthly database."""
        try:
            self.execute_master(
                "UPDATE monthly_database_registry SET last_access_date = CURRENT_TIMESTAMP WHERE month_period = :month_period",
                {"month_period": year_month},
            )
        except Exception as e:
            logger.warning(f"Failed to update access time for {year_month}: {e}")

    # Backup Operations
    def backup_master_database(self) -> Path:
        """Create backup of master database."""
        try:
            backup_path = self.config.get_backup_path("master")

            if not self.config.MASTER_DB_FILE.exists():
                raise FileNotFoundError("Master database file not found")

            shutil.copy2(self.config.MASTER_DB_FILE, backup_path)

            if self.config.BACKUP_COMPRESSION:
                # TODO: Implement backup compression using gzip or similar
                pass

            logger.info(f"Master database backed up to: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Master database backup failed: {e}")
            raise QueryError(f"Backup failed: {e}") from e

    def backup_monthly_database(self, year_month: str) -> Path:
        """Create backup of monthly database."""
        try:
            backup_path = self.config.get_backup_path("monthly", year_month)
            monthly_db_path = self.config.get_monthly_database_path(year_month)

            if not monthly_db_path.exists():
                raise FileNotFoundError(f"Monthly database not found: {year_month}")

            shutil.copy2(monthly_db_path, backup_path)

            logger.info(f"Monthly database {year_month} backed up to: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Monthly database backup failed for {year_month}: {e}")
            raise QueryError(f"Monthly backup failed: {e}") from e

    def archive_monthly_database(self, year_month: str) -> None:
        """Archive monthly database (backup and mark as archived)."""
        try:
            # Create backup first
            self.backup_monthly_database(year_month)

            # Update registry status
            self.execute_master(
                "UPDATE monthly_database_registry SET status = 'ARCHIVED' WHERE month_period = :month_period",
                {"month_period": year_month},
            )

            logger.info(f"Monthly database {year_month} archived successfully")

        except Exception as e:
            logger.error(f"Monthly database archival failed for {year_month}: {e}")
            raise QueryError(f"Archive failed: {e}") from e

    def cleanup_old_databases(
        self, retention_months: int = DatabaseConfig.BACKUP_RETENTION_MONTHS
    ) -> list[str]:
        """Cleanup old monthly databases based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_months * 30)
            cutoff_period = cutoff_date.strftime("%Y-%m")

            # Get old databases
            old_periods = []
            for period in self.config.list_monthly_databases():
                if period < cutoff_period:
                    old_periods.append(period)

            # Archive old databases
            for period in old_periods:
                try:
                    self.archive_monthly_database(period)
                    logger.info(f"Archived old database: {period}")
                except Exception as e:
                    logger.warning(f"Failed to archive {period}: {e}")

            return old_periods

        except Exception as e:
            logger.error(f"Database cleanup failed: {e}")
            return []

    # Utility Methods
    def get_database_info(self) -> dict[str, Any]:
        """Get comprehensive database information."""
        try:
            info: dict[str, Any] = {
                "master_database": {
                    "file_path": str(self.config.MASTER_DB_FILE),
                    "file_exists": self.config.MASTER_DB_FILE.exists(),
                    "file_size": self.config.get_database_file_size(
                        self.config.MASTER_DB_FILE
                    ),
                    "connection_url": self.config.get_master_database_url(),
                },
                "monthly_databases": {},
                "backup_info": {
                    "backup_directory": str(self.config.BACKUP_DIR),
                    "retention_months": self.config.BACKUP_RETENTION_MONTHS,
                    "auto_backup_enabled": self.config.AUTO_BACKUP_ENABLED,
                },
            }

            # Get monthly database info
            for period in self.config.list_monthly_databases():
                db_path = self.config.get_monthly_database_path(period)
                info["monthly_databases"][period] = {
                    "file_path": str(db_path),
                    "file_size": self.config.get_database_file_size(db_path),
                    "status": self._get_database_status(period),
                }

            # Get table counts
            if self.config.MASTER_DB_FILE.exists():
                master_tables = self.query_master(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
                    ttl=0,
                )
                info["master_database"]["table_count"] = len(master_tables)

            return info

        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}

    def _get_database_status(self, year_month: str) -> str:
        """Get database status from registry."""
        try:
            result = self.query_master(
                "SELECT status FROM monthly_database_registry WHERE month_period = :month_period",
                ttl=0,
                params={"month_period": year_month},
            )
            return result.iloc[0]["status"] if not result.empty else "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    def reset_all_databases(self) -> None:
        """Reset all databases (master and monthly)."""
        try:
            logger.info("Resetting all databases...")

            # Reset master database
            if self.config.MASTER_DB_FILE.exists():
                self.config.MASTER_DB_FILE.unlink()

            # Reset monthly databases
            if self.config.MONTHLY_DB_DIR.exists():
                shutil.rmtree(self.config.MONTHLY_DB_DIR)

            # Reset connections
            self._master_connection = None
            self._monthly_connections.clear()

            # Reinitialize
            self._setup_databases()

            logger.info("All databases reset completed")

        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            raise SchemaError(f"Reset failed: {e}") from e

    def reset_connections(self) -> None:
        """Reset all database connections."""
        try:
            if self._master_connection is not None:
                self._master_connection.reset()

            for conn in self._monthly_connections.values():
                conn.reset()

            # Clear connection cache
            self._master_connection = None
            self._monthly_connections.clear()

            logger.info("All connections reset successfully")

        except Exception as e:
            logger.error(f"Connection reset failed: {e}")


@st.cache_resource
def get_database_manager() -> DatabaseManager:
    """Get cached database manager instance."""
    return DatabaseManager()


def init_database() -> DatabaseManager:
    """Initialize enhanced database manager."""
    return get_database_manager()
