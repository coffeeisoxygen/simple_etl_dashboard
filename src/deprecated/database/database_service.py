"""Updated Database Service - Fresh Schema Implementation.

Focused on 6 requirements:
1. Proper database system
2. Essential utilities without over-engineering
3. Admin seeding
4. Streamlit re-run safety
5. Database reset capability
6. Safe CRUD operations
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from loguru import logger
from sqlalchemy import text
from src.database.db_config import DatabaseConfig
from src.database.db_exceptions import ConnectionError, DatabaseError, QueryError
from src.database.db_schema import DatabaseSchema
from streamlit.connections import SQLConnection


class DatabaseService:
    """Simplified database service - essential operations only."""

    def __init__(self, config: DatabaseConfig | None = None) -> None:
        """Initialize database service."""
        self.config = config or DatabaseConfig()
        self._connection: SQLConnection | None = None

        # Initialize once per Streamlit session
        self._ensure_initialized()

    def _ensure_initialized(self) -> None:
        """Ensure database is initialized - Streamlit re-run safe."""
        init_key = "database_initialized"

        if st.session_state.get(init_key, False):
            logger.debug("Database already initialized this session")
            return

        try:
            logger.info("Initializing database...")

            # Ensure directories
            self.config.ensure_directories()

            # Test connection
            conn = self._get_connection()
            result = conn.query("SELECT 1 as test", ttl=0)

            if result.empty or result.iloc[0]["test"] != 1:
                raise ConnectionError("Database connection test failed")

            # Create schema if needed
            self._ensure_schema()

            # Seed admin if needed
            self._ensure_admin_user()

            # Mark as initialized
            st.session_state[init_key] = True
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Database initialization failed: {e}") from e

    def _ensure_schema(self) -> None:
        """Create NEW database schema - fresh implementation."""
        try:
            # FRESH START: Clean old schema first
            logger.info("🧹 Cleaning deprecated tables...")
            DatabaseSchema.cleanup_old_schema(self)

            # Check NEW tables
            tables_result = self.query(
                "SELECT name FROM sqlite_master WHERE type='table'", ttl=0
            )

            expected_tables = set(DatabaseSchema.get_expected_table_names())
            existing_tables = set(tables_result["name"].tolist())
            missing_tables = expected_tables - existing_tables

            if missing_tables:
                logger.info(f"🏗️ Creating NEW tables: {missing_tables}")
                self._create_new_schema()
                logger.info("✅ NEW database schema created")

        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            raise DatabaseError(f"Schema creation failed: {e}") from e

    def _create_new_schema(self) -> None:
        """Create NEW business-focused schema."""
        conn = self._get_connection()

        with conn.session as session:
            # Create NEW tables
            for table_sql in DatabaseSchema.get_core_tables():
                session.execute(text(table_sql))

            # Create NEW indexes
            for index_sql in DatabaseSchema.get_core_indexes():
                session.execute(text(index_sql))

            session.commit()
            logger.info("🎉 NEW schema implementation completed")

    def _ensure_admin_user(self) -> None:
        """Seed admin user - updated for NEW schema."""
        try:
            # Check if admin exists in NEW users table
            admin_result = self.query(
                "SELECT id FROM users WHERE username = 'admin'", ttl=0
            )

            if not admin_result.empty:
                logger.debug("Admin user already exists")
                return

            # Create admin user in NEW table
            admin_hash = hashlib.sha256(b"admin123").hexdigest()

            self.execute(
                """INSERT INTO users (username, password_hash, is_admin, is_active)
                   VALUES (:username, :password_hash, 1, 1)""",
                {
                    "username": "admin",
                    "password_hash": admin_hash,
                },
            )

            logger.info("👤 Admin user created (username: admin, password: admin123)")

        except Exception as e:
            logger.error(f"Admin user creation failed: {e}")
            raise DatabaseError(f"Admin user creation failed: {e}") from e

    def _get_connection(self) -> SQLConnection:
        """Get database connection with caching."""
        if self._connection is None:
            try:
                self._connection = st.connection(
                    self.config.CONNECTION_NAME,
                    type="sql",
                    url=self.config.get_database_url(),
                    **self.config.get_connection_config(),
                )
                logger.debug("Database connection established")
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                raise ConnectionError(f"Failed to connect: {e}") from e

        return self._connection

    # ================================
    # CORE CRUD OPERATIONS
    # ================================

    def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        ttl: int = DatabaseConfig.DEFAULT_TTL,
        **kwargs,
    ) -> pd.DataFrame:
        """Execute SELECT query safely with optional caching."""
        try:
            conn = self._get_connection()

            if params:
                result = conn.query(sql, ttl=ttl, params=params, **kwargs)
            else:
                result = conn.query(sql, ttl=ttl, **kwargs)

            logger.debug(f"Query executed: {len(result)} rows")
            return result

        except Exception as e:
            logger.error(f"Query failed: {sql[:50]}... - {e}")
            raise QueryError(f"Query failed: {e}") from e

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> int:
        """Execute INSERT/UPDATE/DELETE safely."""
        try:
            conn = self._get_connection()

            with conn.session as session:
                if params:
                    result = session.execute(text(sql), params)
                else:
                    result = session.execute(text(sql))
                session.commit()

                # Return affected rows for INSERT/UPDATE/DELETE
                return result.rowcount

        except Exception as e:
            logger.error(f"Execute failed: {sql[:50]}... - {e}")
            raise QueryError(f"Execute failed: {e}") from e

    def execute_many(self, sql: str, params_list: list[dict[str, Any]]) -> int:
        """Execute batch operations safely."""
        try:
            conn = self._get_connection()
            total_affected = 0

            with conn.session as session:
                for params in params_list:
                    result = session.execute(text(sql), params)
                    total_affected += result.rowcount
                session.commit()

            logger.info(f"Batch executed: {len(params_list)} operations")
            return total_affected

        except Exception as e:
            logger.error(f"Batch execute failed: {e}")
            raise QueryError(f"Batch execute failed: {e}") from e

    # ================================
    # SAFE QUERY BUILDERS
    # ================================

    def select(
        self,
        table: str,
        columns: list[str] | str = "*",
        where: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
        ttl: int = DatabaseConfig.DEFAULT_TTL,
    ) -> pd.DataFrame:
        """Safe SELECT query builder."""
        try:
            # Build column list
            if isinstance(columns, list):
                columns_str = ", ".join(columns)
            else:
                columns_str = columns

            # Build base query
            sql_parts = [f"SELECT {columns_str} FROM {table}"]
            params = {}

            # Add WHERE clause
            if where:
                where_parts = []
                for key, value in where.items():
                    param_key = f"where_{key}"
                    where_parts.append(f"{key} = :{param_key}")
                    params[param_key] = value
                sql_parts.append(f"WHERE {' AND '.join(where_parts)}")

            # Add ORDER BY
            if order_by:
                sql_parts.append(f"ORDER BY {order_by}")

            # Add LIMIT
            if limit:
                sql_parts.append(f"LIMIT {limit}")

            sql = " ".join(sql_parts)
            return self.query(sql, params, ttl)

        except Exception as e:
            logger.error(f"Select query builder failed: {e}")
            raise QueryError(f"Select failed: {e}") from e

    def insert(self, table: str, data: dict[str, Any]) -> int:
        """Safe INSERT query builder."""
        try:
            columns = list(data.keys())
            placeholders = [f":{col}" for col in columns]

            sql = f"""
                INSERT INTO {table} ({", ".join(columns)})
                VALUES ({", ".join(placeholders)})
            """

            return self.execute(sql, data)

        except Exception as e:
            logger.error(f"Insert failed for table {table}: {e}")
            raise QueryError(f"Insert failed: {e}") from e

    def update(
        self,
        table: str,
        data: dict[str, Any],
        where: dict[str, Any],
    ) -> int:
        """Safe UPDATE query builder."""
        try:
            # Build SET clause
            set_parts = []
            params = {}

            for key, value in data.items():
                param_key = f"set_{key}"
                set_parts.append(f"{key} = :{param_key}")
                params[param_key] = value

            # Build WHERE clause
            where_parts = []
            for key, value in where.items():
                param_key = f"where_{key}"
                where_parts.append(f"{key} = :{param_key}")
                params[param_key] = value

            sql = f"""
                UPDATE {table}
                SET {", ".join(set_parts)}
                WHERE {" AND ".join(where_parts)}
            """

            return self.execute(sql, params)

        except Exception as e:
            logger.error(f"Update failed for table {table}: {e}")
            raise QueryError(f"Update failed: {e}") from e

    def delete(
        self,
        table: str,
        where: dict[str, Any],
    ) -> int:
        """Safe DELETE query builder."""
        try:
            # Build WHERE clause
            where_parts = []
            params = {}

            for key, value in where.items():
                param_key = f"where_{key}"
                where_parts.append(f"{key} = :{param_key}")
                params[param_key] = value

            sql = f"""
                DELETE FROM {table}
                WHERE {" AND ".join(where_parts)}
            """

            return self.execute(sql, params)

        except Exception as e:
            logger.error(f"Delete failed for table {table}: {e}")
            raise QueryError(f"Delete failed: {e}") from e

    # ================================
    # ESSENTIAL UTILITIES
    # ================================

    def check_health(self) -> dict[str, Any]:
        """Simple health check."""
        try:
            # Connection test
            result = self.query("SELECT 1 as test", ttl=0)

            if result.empty or result.iloc[0]["test"] != 1:
                return {
                    "status": "unhealthy",
                    "message": "Connection test failed",
                    "timestamp": datetime.now().isoformat(),
                }

            # Schema test
            tables = self.query(
                "SELECT name FROM sqlite_master WHERE type='table'", ttl=0
            )
            expected_tables = set(DatabaseSchema.get_expected_table_names())
            existing_tables = set(tables["name"].tolist())
            missing_tables = expected_tables - existing_tables

            if missing_tables:
                return {
                    "status": "degraded",
                    "message": f"Missing tables: {', '.join(missing_tables)}",
                    "timestamp": datetime.now().isoformat(),
                }

            return {
                "status": "healthy",
                "message": "All checks passed",
                "tables_count": len(existing_tables),
                "database_size_mb": round(self.get_database_size() / 1024 / 1024, 2),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    def get_database_size(self) -> int:
        """Get database file size in bytes."""
        return self.config.get_database_file_size()

    def reset_database(self) -> bool:
        """⚠️ DESTRUCTIVE: Reset entire database."""
        try:
            logger.warning("Resetting database - all data will be lost")

            # Clear session state
            if "database_initialized" in st.session_state:
                del st.session_state["database_initialized"]

            # Reset connection
            self._connection = None

            # Remove database file
            if self.config.DB_FILE.exists():
                self.config.DB_FILE.unlink()

            # Reinitialize
            self._ensure_initialized()

            logger.warning("Database reset completed")
            return True

        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            return False

    def create_backup(self, backup_name: str | None = None) -> Path:
        """Create simple database backup."""
        import shutil

        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}.db"

            backup_path = self.config.get_backup_path(backup_name)
            shutil.copy2(self.config.DB_FILE, backup_path)

            logger.info(f"Backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise DatabaseError(f"Backup failed: {e}") from e

    # ================================
    # AUTH UTILITIES
    # ================================

    def verify_user(self, username: str, password: str) -> dict[str, Any] | None:
        """Verify user credentials - updated for NEW schema."""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            result = self.query(
                """SELECT id, username, is_admin, is_active
                   FROM users  -- Updated table name
                   WHERE username = :username
                   AND password_hash = :password_hash
                   AND is_active = 1""",
                {
                    "username": username,
                    "password_hash": password_hash,
                },
                ttl=0,
            )

            if result.empty:
                return None

            user_data = result.iloc[0].to_dict()
            logger.info(f"👤 User verified: {username}")
            return user_data

        except Exception as e:
            logger.error(f"User verification failed: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """Get user by ID - updated for NEW schema."""
        try:
            result = self.select(
                "users",  # Updated table name
                columns=["id", "username", "is_admin", "is_active"],
                where={"id": user_id, "is_active": 1},
                ttl=DatabaseConfig.LONG_TTL,
            )

            if result.empty:
                return None

            return result.iloc[0].to_dict()

        except Exception as e:
            logger.error(f"Get user by ID failed: {e}")
            return None


# ================================
# GLOBAL SERVICE INSTANCE
# ================================


@st.cache_resource
def get_database_service() -> DatabaseService:
    """Get cached database service instance."""
    return DatabaseService()


# TODO: Add simple data seeding utilities
# PINNED: Consider adding table migration helpers if needed
# REMINDER: Keep it simple - focus on 6 core requirements!
