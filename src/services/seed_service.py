"""Seed service for database initialization and sample data management.

Handles all seeding operations including admin user creation, sample data,
and development/testing data seeding with proper validation.
"""

from loguru import logger

from repositories.auth.sql_user_repository import SQLUserRepository
from schemas.auth.request import RegisterUserRequest
from services.auth_service import register


class SeedService:
    """Service for handling database seeding operations."""

    def __init__(self) -> None:
        """Initialize seed service with repository."""
        self.user_repo = SQLUserRepository()

    def seed_admin_user(
        self,
        username: str = "admin",
        password: str = "admin123",
        name: str = "Super Admin",
    ) -> bool:
        """Seed admin user using auth service for consistency.

        Args:
            username: Admin username
            password: Admin password
            name: Admin display name

        Returns:
            True if seeding successful, False otherwise
        """
        try:
            logger.info(f"Seeding admin user: {username}")

            # Check if admin user already exists
            existing_admin = self.user_repo.get_by_username(username)

            if existing_admin is None:
                logger.info(f"Creating admin user: {username}")

                # Use auth service for proper validation and creation
                admin_data = RegisterUserRequest(
                    username=username,
                    name=name,
                    password=password,
                    is_admin=True,
                    is_active=True,
                )

                register(admin_data, self.user_repo)
                logger.success(f"✅ Admin user created: {username}/{password}")
                return True
            else:
                logger.info(f"Admin user '{username}' already exists, skipping")
                return True

        except Exception as e:
            logger.error(f"Failed to seed admin user: {e}")
            return False

    def seed_sample_data(self) -> bool:
        """Seed sample data for development and testing.

        Returns:
            True if seeding successful, False otherwise
        """
        try:
            logger.info("Seeding sample data...")

            # TODO: Add sample CSV data, test users, etc.
            # For now, just return True

            logger.success("✅ Sample data seeding completed")
            return True

        except Exception as e:
            logger.error(f"Failed to seed sample data: {e}")
            return False

    def reset_and_seed(self) -> bool:
        """Reset database and seed fresh data.

        PINNED: Implement for development/testing needs

        Returns:
            True if reset and seeding successful, False otherwise
        """
        try:
            logger.info("Resetting database and seeding fresh data...")

            # TODO: Implement database reset logic if needed
            # For now, just run normal seeding

            return self.seed_all()

        except Exception as e:
            logger.error(f"Failed to reset and seed: {e}")
            return False

    def seed_all(self) -> bool:
        """Main entry point for all seeding operations.

        Returns:
            True if all seeding successful, False otherwise
        """
        try:
            logger.info("Starting comprehensive database seeding...")

            # Step 1: Seed admin user
            if not self.seed_admin_user():
                logger.error("Admin user seeding failed")
                return False

            # Step 2: Seed sample data (optional, won't fail initialization)
            if not self.seed_sample_data():
                logger.warning("Sample data seeding failed, but continuing...")

            logger.success("✅ Database seeding completed successfully")
            return True

        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
            logger.exception("Full seeding error traceback:")
            return False


# Global instance management (following existing pattern)
_seed_service: SeedService | None = None


def get_seed_service() -> SeedService:
    """Get the global seed service instance.

    Returns:
        Global seed service instance
    """
    global _seed_service
    if _seed_service is None:
        _seed_service = SeedService()
        logger.debug("Created global seed service instance")
    return _seed_service


# Convenience functions for common operations
def seed_admin_user(
    username: str = "admin", password: str = "admin123", name: str = "Super Admin"
) -> bool:
    """Convenience function to seed admin user.

    Args:
        username: Admin username
        password: Admin password
        name: Admin display name

    Returns:
        True if seeding successful, False otherwise
    """
    return get_seed_service().seed_admin_user(username, password, name)


def seed_all() -> bool:
    """Convenience function for complete seeding.

    Returns:
        True if all seeding successful, False otherwise
    """
    return get_seed_service().seed_all()


def reset_and_seed() -> bool:
    """Convenience function to reset and seed database.

    Returns:
        True if reset and seeding successful, False otherwise
    """
    return get_seed_service().reset_and_seed()
