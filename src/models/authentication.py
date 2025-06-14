"""Authentication models untuk user management dan login system."""

from datetime import datetime

import bcrypt
from pydantic import BaseModel, Field, field_validator

from src.models.commons import DatabaseEntity, OperationResult, ValidationMixin


class User(DatabaseEntity):
    """Model untuk admin user dalam aplikasi ETL Dashboard.

    Untuk MVP, fokus ke single admin user dengan seed data dan password management.
    """

    username: str = Field(
        ..., min_length=3, max_length=50, description="Username admin"
    )
    password_hash: str = Field(..., description="Hashed password")
    is_admin: bool = Field(default=True, description="Admin status")
    is_active: bool = Field(default=True, description="User active status")
    last_login: datetime | None = Field(
        default=None, description="Last login timestamp"
    )

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        """Normalize username ke lowercase untuk konsistensi."""
        return ValidationMixin.validate_not_empty(v, "Username").lower()

    @field_validator("password_hash")
    @classmethod
    def validate_password_hash(cls, v: str) -> str:
        """Validate password hash tidak kosong."""
        return ValidationMixin.validate_not_empty(v, "Password hash")


class UserCreate(BaseModel):
    """Model untuk create admin user (seed scenario)."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(
        ..., min_length=6, max_length=100, description="Plain password"
    )
    is_admin: bool = Field(default=True, description="Admin status")
    is_active: bool = Field(default=True, description="Active status")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        """Normalize username ke lowercase."""
        return ValidationMixin.validate_not_empty(v, "Username").lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength dengan rules sederhana."""
        ValidationMixin.validate_min_length(v, 6, "Password")

        if v.isdigit():
            raise ValueError("Password tidak boleh hanya angka")
        if v.isalpha() and len(v) < 8:
            raise ValueError("Password hanya huruf minimal 8 karakter")

        return v

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class UserUpdate(BaseModel):
    """Model untuk update user data (fokus ke password change)."""

    username: str | None = Field(None, min_length=3, max_length=50)
    password: str | None = Field(None, min_length=6, max_length=100)
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str | None) -> str | None:
        """Normalize username jika ada."""
        if v is None:
            return v
        return ValidationMixin.validate_not_empty(v, "Username").lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str | None) -> str | None:
        """Validate password strength jika ada update."""
        if v is None:
            return v

        ValidationMixin.validate_min_length(v, 6, "Password")

        if v.isdigit():
            raise ValueError("Password tidak boleh hanya angka")
        if v.isalpha() and len(v) < 8:
            raise ValueError("Password hanya huruf minimal 8 karakter")

        return v

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
    }


class UserResponse(BaseModel):
    """Model untuk response user data tanpa sensitive information."""

    id: int
    username: str
    is_admin: bool
    is_active: bool
    act_date: datetime
    last_login: datetime | None = None

    model_config = {
        "from_attributes": True,
        "str_strip_whitespace": True,
    }


class LoginRequest(BaseModel):
    """Model untuk login request."""

    username: str = Field(..., min_length=1, max_length=50, description="Username")
    password: str = Field(..., min_length=1, max_length=100, description="Password")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        """Normalize username untuk login."""
        return ValidationMixin.validate_not_empty(v, "Username").lower()

    @field_validator("password")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        """Validate password tidak kosong."""
        return ValidationMixin.validate_not_empty(v, "Password")

    model_config = {
        "str_strip_whitespace": True,
    }


class LoginResponse(BaseModel):
    """Model untuk login response dengan session info."""

    user: UserResponse
    session_token: str
    expires_at: datetime
    message: str


class PasswordChangeRequest(BaseModel):
    """Model untuk password change request."""

    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(
        ..., min_length=6, max_length=100, description="New password"
    )

    @field_validator("current_password")
    @classmethod
    def validate_current_password(cls, v: str) -> str:
        """Validate current password tidak kosong."""
        return ValidationMixin.validate_not_empty(v, "Current password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        """Validate new password strength."""
        ValidationMixin.validate_min_length(v, 6, "New password")

        if v.isdigit():
            raise ValueError("Password baru tidak boleh hanya angka")
        if v.isalpha() and len(v) < 8:
            raise ValueError("Password baru hanya huruf minimal 8 karakter")

        return v

    model_config = {
        "str_strip_whitespace": True,
    }


class PasswordHash:
    """Utility class untuk password hashing dengan bcrypt."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password dengan bcrypt salt."""
        salt = bcrypt.gensalt()
        password_bytes = password.encode("utf-8")
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verify password dengan stored hash."""
        try:
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False

    @staticmethod
    def is_password_secure(password: str) -> tuple[bool, str]:
        """Check apakah password memenuhi security requirements."""
        if len(password) < 6:
            return False, "Password minimal 6 karakter"

        if password.isdigit():
            return False, "Password tidak boleh hanya angka"

        if password.isalpha() and len(password) < 8:
            return False, "Password hanya huruf minimal 8 karakter"

        return True, "Password memenuhi requirements"


class AdminSeedData:
    """Default admin data untuk seed scenario."""

    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "admin123"
    FORCE_CHANGE_PASSWORD = True

    @classmethod
    def create_default_admin(cls) -> UserCreate:
        """Create default admin user untuk seed."""
        return UserCreate(
            username=cls.DEFAULT_USERNAME,
            password=cls.DEFAULT_PASSWORD,
            is_admin=True,
            is_active=True,
        )

    @classmethod
    def should_force_password_change(cls, user: User) -> bool:
        """Check apakah user harus ganti password (default password)."""
        if not cls.FORCE_CHANGE_PASSWORD:
            return False

        # Check apakah masih menggunakan default password
        return user.username == cls.DEFAULT_USERNAME and PasswordHash.verify_password(
            cls.DEFAULT_PASSWORD, user.password_hash
        )


class AuthenticationRules:
    """Business rules untuk authentication system."""

    @staticmethod
    def can_change_password(user: User, current_user: User) -> OperationResult[bool]:
        """Check apakah user bisa change password."""
        if user.id != current_user.id:
            return OperationResult.error_result(
                message="Hanya bisa mengubah password sendiri",
                error_code="UNAUTHORIZED_PASSWORD_CHANGE",
            )

        if not user.is_active:
            return OperationResult.error_result(
                message="User tidak aktif", error_code="INACTIVE_USER"
            )

        return OperationResult.success_result(
            data=True, message="Password dapat diubah"
        )

    @staticmethod
    def validate_login_attempt(
        username: str, user: User | None
    ) -> OperationResult[bool]:
        """Validate login attempt."""
        if user is None:
            return OperationResult.error_result(
                message="Username tidak ditemukan", error_code="USER_NOT_FOUND"
            )

        if not user.is_active:
            return OperationResult.error_result(
                message="User tidak aktif", error_code="INACTIVE_USER"
            )

        return OperationResult.success_result(data=True, message="Login attempt valid")
