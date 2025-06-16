"""Database engine setup following SQLAlchemy v2 best practices."""

from pathlib import Path

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_database_engine(db_path: Path | None = None) -> Engine:
    """Create SQLAlchemy engine with optimized settings.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Configured SQLAlchemy engine
    """
    # Default database path
    if db_path is None:
        db_path = Path("data") / "etl_dashboard.db"

    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Create engine with SQLAlchemy v2 settings
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,  # Set to True for SQL debugging
        future=True,  # Use SQLAlchemy v2 future mode
        # SQLite optimizations
        connect_args={
            "check_same_thread": False,  # Allow multithreading
            "timeout": 30,  # Connection timeout
        },
        # Connection pool settings
        pool_pre_ping=True,  # Verify connections
        pool_recycle=3600,  # Recycle after 1 hour
    )

    logger.debug(f"Database engine created: {db_path}")
    return engine
