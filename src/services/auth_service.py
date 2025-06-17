"""Authentication Service Module.

This module provides core authentication functionality for the ETL Dashboard application.
It handles user login, registration, password management, and user account status management.

Key Features:
- User authentication with username/password
- User registration with role-based access
- Password change functionality with verification
- User account deactivation (except admin users)

Dependencies:
- User model for database operations
- Repository pattern for data access
- Password hashing utilities for security
- Pydantic schemas for request/response validation

Note:
- All functions use dependency injection pattern with IUserRepository
- Error handling uses ValueError for business logic violations
- Admin users have special protection against deactivation
"""

from models.user_model import User
from protocols.auth.user_repository import IUserRepository
from schemas.auth.request import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterUserRequest,
)
from schemas.auth.response import LoginResponse
from utils.hashing import hash_password, verify_password


def login(data: LoginRequest, repo: IUserRepository) -> LoginResponse:
    """Authenticate user with username and password.

    Validates user credentials and returns user information if authentication
    is successful. Checks for user existence, active status, and password match.

    Args:
        data: Login request containing username and password
        repo: User repository interface for database operations

    Returns:
        LoginResponse: User information including username, name, and admin status

    Raises:
        ValueError: If login fails due to:
            - User not found
            - User account is inactive
            - Password verification fails

    Example:
        >>> login_req = LoginRequest(
        ...     username="admin", password="password123"
        ... )
        >>> user_info = login(login_req, user_repository)
        >>> print(user_info.username)  # "admin"
    """
    user = repo.get_by_username(data.username)
    if (
        not user
        or not user.is_active
        or not verify_password(data.password, user.password_hash)
    ):
        raise ValueError("Login gagal")

    return LoginResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        is_admin=user.is_admin,
        is_active=user.is_active,
    )


def register(data: RegisterUserRequest, repo: IUserRepository) -> None:
    """Register a new user account.

    Creates a new user with the provided information after validating
    that the username is not already taken. Passwords are automatically
    hashed before storage.

    Args:
        data: Registration request containing user details
        repo: User repository interface for database operations

    Raises:
        ValueError: If username is already taken

    Note:
        - Passwords are automatically hashed using secure hashing
        - Admin status and active status are configurable during registration
        - Username must be unique across the system

    Example:
        >>> reg_req = RegisterUserRequest(
        ...     username="newuser",
        ...     name="New User",
        ...     password="secure123",
        ...     is_admin=False,
        ...     is_active=True,
        ... )
        >>> register(reg_req, user_repository)
    """
    if repo.get_by_username(data.username):
        raise ValueError("Username sudah digunakan")

    new_user = User(
        username=data.username,
        name=data.name,
        password_hash=hash_password(data.password),
        is_admin=data.is_admin,
        is_active=data.is_active,
    )
    repo.add_user(new_user)


def change_password(data: ChangePasswordRequest, repo: IUserRepository) -> None:
    """Change user's password with old password verification.

    Updates user's password after verifying the old password is correct.
    The new password is automatically hashed before storage.

    Args:
        data: Password change request containing user ID and passwords
        repo: User repository interface for database operations

    Raises:
        ValueError: If:
            - User not found
            - Old password verification fails

    Security:
        - Requires old password verification before change
        - New password is securely hashed
        - No password history or complexity validation (FUTURE enhancement)

    Example:
        >>> pwd_req = ChangePasswordRequest(
        ...     id=1,
        ...     old_password="oldpass123",
        ...     new_password="newpass456",
        ... )
        >>> change_password(pwd_req, user_repository)
    """
    user = repo.get_by_id(data.id)
    if not user or not verify_password(data.old_password, user.password_hash):
        raise ValueError("Password lama salah")

    user.password_hash = hash_password(data.new_password)
    repo.update(user)


def deactivate_user(user_id: int, repo: IUserRepository) -> None:
    """Deactivate a user account.

    Sets user's active status to False, effectively disabling their account.
    Admin users are protected from deactivation to maintain system access.

    Args:
        user_id: ID of the user to deactivate
        repo: User repository interface for database operations

    Raises:
        ValueError: If:
            - User not found
            - Attempting to deactivate an admin user

    Business Rules:
        - Admin users cannot be deactivated (system protection)
        - Deactivated users cannot login
        - Deactivation is reversible (can be reactivated later)

    Example:
        >>> deactivate_user(123, user_repository)
        # User 123 is now inactive and cannot login

    Note:
        For reactivation, directly update user.is_active = True via repository
    """
    user = repo.get_by_id(user_id)
    if not user or user.is_admin:
        raise ValueError("Tidak bisa nonaktifkan admin")

    user.is_active = False
    repo.update(user)
