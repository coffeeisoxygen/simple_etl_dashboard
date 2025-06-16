"""Test configuration and shared fixtures for the ETL Dashboard.

This module provides shared test fixtures including in-memory database setup,
repository instances, and common test data for efficient testing.
"""

import pytest
from sqlalchemy import create_engine

from database.session import SessionManager
from models import Base
from repositories.sql_userrepo import SQLUserRepository


@pytest.fixture(scope="function")
def memory_engine():
    """Create in-memory SQLite engine for testing.

    This fixture creates a fresh SQLite in-memory database for each test,
    ensuring complete test isolation without I/O overhead.

    Returns:
        SQLAlchemy Engine configured for in-memory SQLite
    """
    engine = create_engine(
        "sqlite:///:memory:",  # In-memory database
        echo=False,  # Set to True for SQL debugging
        future=True,  # SQLAlchemy v2 mode
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    return engine


@pytest.fixture(scope="function")
def memory_session_manager(memory_engine):
    """Create session manager with in-memory database.

    Args:
        memory_engine: In-memory SQLite engine

    Returns:
        SessionManager instance for testing
    """
    return SessionManager(memory_engine)


@pytest.fixture(scope="function")
def memory_repo(memory_session_manager):
    """Create repository instance with in-memory database.

    Args:
        memory_session_manager: Session manager with in-memory database

    Returns:
        SQLUserRepository instance for testing
    """

    # Create a test database service wrapper that mimics get_db_session()
    class TestDatabaseService:
        def __init__(self, session_manager):
            self.session_manager = session_manager
            self.engine = session_manager.engine

        def session_scope(self):
            return self.session_manager.session_scope()

        def batch_session(self):
            return self.session_manager.batch_session()

    test_db_service = TestDatabaseService(memory_session_manager)

    # Create repository with our test database service
    class TestSQLUserRepository(SQLUserRepository):
        def __init__(self, db_service):
            self.db = db_service

    return TestSQLUserRepository(test_db_service)


@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing.

    Returns:
        Dictionary with sample user information
    """
    return {
        "username": "testuser",
        "name": "Test User",
        "password": "testpass123",
        "is_admin": False,
        "is_active": True,
    }


@pytest.fixture
def admin_user_data():
    """Provide admin user data for testing.

    Returns:
        Dictionary with admin user information
    """
    return {
        "username": "admin",
        "name": "Admin User",
        "password": "admin123",
        "is_admin": True,
        "is_active": True,
    }
