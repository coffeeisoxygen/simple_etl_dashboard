"""Models package with all database models."""

from .base import Base
from .user_model import User  # ✅ FIXED: Import from user_model, not user

# Export all models for easy importing
__all__ = [
    "Base",
    "User",
]

# FUTURE: Add ETL models here
# from .retailer import Retailer
# from .transaction import Transaction
