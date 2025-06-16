"""Session management following SQLAlchemy v2 best practices."""

from collections.abc import Generator
from contextlib import contextmanager

from loguru import logger
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


class SessionManager:
    """Session manager for database operations.

    Provides clean session management with proper transaction handling.
    """

    def __init__(self, engine: Engine) -> None:
        """Initialize session manager with engine."""
        self.engine = engine
        self.SessionLocal = sessionmaker(
            bind=engine,
            autoflush=False,
            autocommit=False,
            future=True,  # SQLAlchemy v2 mode
        )

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide session with automatic transaction management.

        This context manager handles:
        - Session creation
        - Automatic commit on success
        - Automatic rollback on error
        - Session cleanup

        Usage:
            with session_manager.session_scope() as session:
                user = session.get(User, 1)
                user.name = "New Name"
                # Auto-commit on exit
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session rolled back due to error: {e}")
            raise
        finally:
            session.close()

    @contextmanager
    def batch_session(self) -> Generator[Session, None, None]:
        """Provide session for batch operations without auto-commit.

        Use this for bulk operations where you want to control
        when commits happen for performance optimization.

        Usage:
            with session_manager.batch_session() as session:
                for batch in batches:
                    session.bulk_insert_mappings(User, batch)
                    if len(batch) > 1000:
                        session.commit()  # Manual commit
                session.commit()  # Final commit
        """
        session = self.SessionLocal()
        try:
            yield session
            # NOTE: No auto-commit - caller controls when to commit
        except Exception as e:
            session.rollback()
            logger.error(f"Batch session rolled back due to error: {e}")
            raise
        finally:
            session.close()
