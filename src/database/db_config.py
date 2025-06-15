"""Database configuration constants - Enhanced with Monthly Partitioning & Backup Support."""

from datetime import datetime
from pathlib import Path
from typing import Any


class DatabaseConfig:
    """Centralized database configuration with monthly partitioning and backup support."""

    # Database directories
    DATA_DIR = Path("data")
    BACKUP_DIR = Path("data/backups")
    MONTHLY_DB_DIR = Path("data/monthly")

    # Master database settings
    MASTER_DB_FILE = DATA_DIR / "sales_dashboard_master.db"
    MASTER_CONNECTION_NAME = "sales_dashboard_master"

    # Monthly database settings
    MONTHLY_DB_PREFIX = "sales_dashboard"
    MONTHLY_CONNECTION_PREFIX = "sales_dashboard_monthly"

    # Connection timeouts and caching
    DEFAULT_TTL = 3600  # 1 hour cache for regular queries
    NO_CACHE_TTL = 0  # No cache for dynamic data
    LONG_TTL = 86400  # 24 hours cache for master data

    # Backup settings
    BACKUP_RETENTION_MONTHS = 12  # Keep backups for 12 months
    AUTO_BACKUP_ENABLED = True
    BACKUP_COMPRESSION = True

    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        cls.MONTHLY_DB_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_master_database_url(cls) -> str:
        """Get master database URL."""
        db_path = cls.MASTER_DB_FILE.resolve()
        return f"sqlite:///{db_path}"

    @classmethod
    def get_monthly_database_path(cls, year_month: str) -> Path:
        """Get monthly database file path for given YYYY-MM."""
        if not year_month or len(year_month) != 7 or year_month[4] != "-":
            raise ValueError(
                f"Invalid year_month format: {year_month}. Expected YYYY-MM"
            )

        filename = f"{cls.MONTHLY_DB_PREFIX}_{year_month}.db"
        return cls.MONTHLY_DB_DIR / filename

    @classmethod
    def get_monthly_database_url(cls, year_month: str) -> str:
        """Get monthly database URL for given YYYY-MM."""
        db_path = cls.get_monthly_database_path(year_month).resolve()
        return f"sqlite:///{db_path}"

    @classmethod
    def get_current_month_period(cls) -> str:
        """Get current month period in YYYY-MM format."""
        return datetime.now().strftime("%Y-%m")

    @classmethod
    def get_monthly_connection_name(cls, year_month: str) -> str:
        """Get connection name for monthly database."""
        return f"{cls.MONTHLY_CONNECTION_PREFIX}_{year_month.replace('-', '_')}"

    @classmethod
    def get_backup_path(cls, database_type: str, year_month: str | None = None) -> Path:
        """Get backup file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if database_type == "master":
            filename = f"master_backup_{timestamp}.db"
        elif database_type == "monthly" and year_month:
            filename = f"monthly_{year_month}_backup_{timestamp}.db"
        else:
            raise ValueError(
                f"Invalid backup parameters: {database_type}, {year_month}"
            )

        return cls.BACKUP_DIR / filename

    @classmethod
    def get_connection_config(cls) -> dict[str, Any]:
        """Get connection configuration for SQLConnection."""
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
    def get_query_config(cls) -> dict[str, Any]:
        """Get default query configuration."""
        return {
            "ttl": cls.DEFAULT_TTL,
            "show_spinner": True,
        }

    @classmethod
    def list_monthly_databases(cls) -> list[str]:
        """List all existing monthly database periods."""
        if not cls.MONTHLY_DB_DIR.exists():
            return []

        periods = []
        pattern = f"{cls.MONTHLY_DB_PREFIX}_*.db"

        for db_file in cls.MONTHLY_DB_DIR.glob(pattern):
            # Extract YYYY-MM from filename
            filename = db_file.stem
            if filename.startswith(f"{cls.MONTHLY_DB_PREFIX}_"):
                period = filename[len(f"{cls.MONTHLY_DB_PREFIX}_") :]
                if len(period) == 7 and period[4] == "-":  # YYYY-MM format
                    periods.append(period)

        return sorted(periods, reverse=True)  # Latest first

    @classmethod
    def get_database_file_size(cls, db_path: Path) -> int:
        """Get database file size in bytes."""
        if db_path.exists():
            return db_path.stat().st_size
        return 0
