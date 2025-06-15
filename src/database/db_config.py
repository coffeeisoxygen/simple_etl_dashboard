"""Database configuration constants."""

from pathlib import Path
from typing import Any


class DatabaseConfig:
    """Centralized database configuration."""

    # Database settings - consistent path
    DB_FILE = Path("data/sales_dashboard.db")
    CONNECTION_NAME = "sales_dashboard"

    # Connection timeouts
    DEFAULT_TTL = 3600
    NO_CACHE_TTL = 0

    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL for connection."""
        # Ensure parent directory exists
        cls.DB_FILE.parent.mkdir(exist_ok=True)
        db_path = cls.DB_FILE.resolve()
        return f"sqlite:///{db_path}"

    @classmethod
    def get_connection_config(cls) -> dict[str, Any]:
        """Get connection configuration for st.connection."""
        return {"url": cls.get_database_url()}
