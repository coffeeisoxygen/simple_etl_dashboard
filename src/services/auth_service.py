"""service untuk mengelola otentikasi pengguna."""

from models.user_model import User
from protocols.user_repository import IUserRepository
from schemas.auth_schema import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterUser,
)
from utils.hashing import hash_password, verify_password


def login(data: LoginRequest, repo: IUserRepository) -> LoginResponse:
    """Login user and return user information.

    This function verifies the user's credentials and returns a response
    containing the user's information if the login is successful.

    Args:
        data (LoginRequest): The login request data.
        repo (IUserRepository): The user repository.

    Raises:
        ValueError: If the login fails.

    Returns:
        LoginResponse: The login response containing user information.
    """
    user = repo.get_by_username(data.username)
    if (
        not user
        or not user.is_active
        or not verify_password(data.password, user.password_hash)
    ):
        raise ValueError("Login gagal")
    return LoginResponse(id=user.id, username=user.username, name=user.name)


def register(data: RegisterUser, repo: IUserRepository) -> None:
    """Register a new user.

    This function creates a new user in the system.

    Args:
        data (RegisterUser): The registration data.
        repo (IUserRepository): The user repository.

    Raises:
        ValueError: If the username is already taken.
    """
    if repo.get_by_username(data.username):
        raise ValueError("Username sudah digunakan")

    # ✅ CONSISTENT: Let database handle timestamp with server_default
    new_user = User(
        username=data.username,
        name=data.name,
        password_hash=hash_password(data.password),
        is_admin=False,
        is_active=True,
        # NOTE: tgl_data handled by server_default=func.current_timestamp()
    )
    repo.add_user(new_user)


def change_password(data: ChangePasswordRequest, repo: IUserRepository) -> None:
    """Change user password.

    Args:
        data (ChangePasswordRequest): Password change request data.
        repo (IUserRepository): The user repository.

    Raises:
        ValueError: If old password is incorrect or user not found.
    """
    user = repo.get_by_id(data.id)
    if not user or not verify_password(data.old_password, user.password_hash):
        raise ValueError("Password lama salah")

    user.password_hash = hash_password(data.new_password)
    repo.update(user)


def deactivate_user(user_id: int, repo: IUserRepository) -> None:
    """Deactivate a user account.

    Args:
        user_id (int): ID of user to deactivate.
        repo (IUserRepository): The user repository.

    Raises:
        ValueError: If user not found or user is admin.
    """
    user = repo.get_by_id(user_id)
    if not user or user.is_admin:
        raise ValueError("Tidak bisa nonaktifkan admin")

    user.is_active = False
    repo.update(user)
