"""Database initialization following SQLAlchemy v2 best practices."""

from pathlib import Path

from loguru import logger
from sqlalchemy import text

from models import Base
from models.user_model import User

from .engine import create_database_engine
from .session import SessionManager


class DatabaseInitializer:
    """Database initializer with clean separation of concerns."""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize database components."""
        self.engine = create_database_engine(db_path)
        self.session_manager = SessionManager(self.engine)

    def create_tables(self) -> bool:
        """Create all database tables from models."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False

    def seed_admin_user(self) -> bool:
        """Create admin user if not exists - business owner optimized.

        Creates admin user with consistent settings for internal tool use.

        Returns:
            True if admin user exists or created successfully
        """
        try:
            with self.session_manager.session_scope() as session:
                # Check if admin exists
                admin = session.query(User).filter_by(username="admin").first()
                if admin:
                    logger.debug("Admin user already exists")
                    return True

                # Create admin user with consistent settings
                from utils.hashing import hash_password

                admin_user = User(
                    username="admin",
                    name="Admin",  # ✅ CONSISTENT: Simple "Admin" name
                    password_hash=hash_password("admin123"),
                    is_admin=True,
                    is_active=True,
                    # ✅ CONSISTENT: Let server_default handle timestamp
                )

                session.add(admin_user)
                logger.info("Admin user created successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to seed admin user: {e}")
            return False

    def health_check(self) -> bool:
        """Verify database connection."""
        try:
            with self.session_manager.session_scope() as session:
                session.execute(text("SELECT 1")).scalar()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def initialize(self) -> bool:
        """Complete database initialization.

        Business owner friendly: handles everything needed for app startup.

        Returns:
            True if all initialization steps successful
        """
        try:
            logger.info("Starting database initialization...")

            # Step 1: Create tables
            if not self.create_tables():
                logger.error("Database initialization failed at table creation")
                return False

            # Step 2: Seed admin user
            if not self.seed_admin_user():
                logger.error("Database initialization failed at admin seeding")
                return False

            # Step 3: Health check
            if not self.health_check():
                logger.error("Database initialization failed at health check")
                return False

            logger.info("Database initialization completed successfully")
            return True

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False


# Convenience functions for easy usage
def initialize_database(db_path: Path | None = None) -> bool:
    """Initialize database - business owner friendly function."""
    initializer = DatabaseInitializer(db_path)
    return initializer.initialize()


def get_session_manager(db_path: Path | None = None) -> SessionManager:
    """Get session manager for database operations."""
    engine = create_database_engine(db_path)
    return SessionManager(engine)
