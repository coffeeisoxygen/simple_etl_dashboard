"""module for storing constants related to the database configuration and connection settings."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DBConstant:
    """Database connection constants.

    This class contains constants related to the database configuration and
    connection settings.
    """

    DATA_DIR = Path("data")
    SQLITE_FILE = DATA_DIR / "sales_dashboard.db"
    SQLITE_URL = f"sqlite:///{SQLITE_FILE.as_posix()}"

    ST_CONN_NAME = "local_sqlite"
    ST_TTL = "10m"


db_const = DBConstant()
