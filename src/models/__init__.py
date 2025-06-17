"""Models package initialization.

Exposes all database models and base classes for clean imports.
Follows the principle of making internal modules easy to import.
"""

from .base import Base
from .user_model import User

# Main exports - what other modules should import
__all__ = [
    "Base",
    "User",
]

# TODO: Add other models here as they are created (ETL jobs, data sources, etc.)
# REMINDER: Keep this file updated when adding new models
