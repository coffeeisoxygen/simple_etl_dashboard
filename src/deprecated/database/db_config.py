"""Enhanced Database Configuration - Essential Settings."""

from pathlib import Path
from typing import Any


class DatabaseConfig:
    """Enhanced database configuration with essential settings."""

    # Database settings
    DATA_DIR = Path("data")
    BACKUP_DIR = Path("data/backups")
    DB_FILE = DATA_DIR / "etl_dashboard.db"
    CONNECTION_NAME = "etl_dashboard"

    # Cache TTL settings
    NO_CACHE_TTL = 0  # No cache for auth/sensitive queries
    SHORT_TTL = 300  # 5 minutes for dynamic data
    DEFAULT_TTL = 3600  # 1 hour for normal data
    LONG_TTL = 86400  # 24 hours for static data

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure required directories exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL for SQLConnection."""
        db_path = cls.DB_FILE.resolve()
        return f"sqlite:///{db_path}"

    @classmethod
    def get_backup_path(cls, backup_name: str) -> Path:
        """Get backup file path."""
        cls.ensure_directories()
        return cls.BACKUP_DIR / backup_name

    @classmethod
    def get_connection_config(cls) -> dict[str, Any]:
        """Get SQLConnection configuration."""
        return {
            "connect_args": {
                "check_same_thread": False,
                "timeout": 30,
            },
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "autocommit": False,
        }

    @classmethod
    def get_database_file_size(cls) -> int:
        """Get database file size in bytes."""
        if cls.DB_FILE.exists():
            return cls.DB_FILE.stat().st_size
        return 0

    @classmethod
    def database_exists(cls) -> bool:
        """Check if database file exists."""
        return cls.DB_FILE.exists()


# TODO: Add environment-specific configs if needed
# REMINDER: Keep configuration simple and essential
