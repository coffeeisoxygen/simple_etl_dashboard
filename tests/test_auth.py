"""Authentication service tests using in-memory SQLite database.

These tests use real database operations with SQLite in-memory for fast,
isolated testing without I/O overhead.
"""

import pytest

from models.user_model import User
from schemas.auth_schema import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterUser,
)
from services.auth_service import (
    change_password,
    deactivate_user,
    login,
    register,
)
from utils.hashing import hash_password


# ✅ Register + Login with real database
def test_register_and_login(memory_repo, sample_user_data):
    """Test user registration and login flow."""
    # Register user
    register_data = RegisterUser(
        username=sample_user_data["username"],
        name=sample_user_data["name"],
        password=sample_user_data["password"],
    )
    register(register_data, memory_repo)

    # Login user
    login_data = LoginRequest(
        username=sample_user_data["username"],
        password=sample_user_data["password"],
    )
    user_response = login(login_data, memory_repo)

    assert user_response.username == sample_user_data["username"]
    assert user_response.name == sample_user_data["name"]
    # Ensure user exists in database
    db_user = memory_repo.get_by_username(sample_user_data["username"])
    assert db_user is not None
    assert db_user.is_active is True


# ❌ Login fails - user not found
def test_login_user_not_found(memory_repo):
    """Test login failure when user doesn't exist."""
    with pytest.raises(ValueError, match="Login gagal"):
        login(LoginRequest(username="nonexistent", password="123"), memory_repo)


# ❌ Login fails - wrong password
def test_login_wrong_password(memory_repo, sample_user_data):
    """Test login failure with wrong password."""
    # Register user first
    register_data = RegisterUser(
        username=sample_user_data["username"],
        name=sample_user_data["name"],
        password=sample_user_data["password"],
    )
    register(register_data, memory_repo)

    # Try login with wrong password
    with pytest.raises(ValueError, match="Login gagal"):
        login(
            LoginRequest(
                username=sample_user_data["username"], password="wrongpassword"
            ),
            memory_repo,
        )


# 🔐 Password change success
def test_change_password_success(memory_repo, sample_user_data):
    """Test successful password change."""
    # Register and login user
    register_data = RegisterUser(
        username=sample_user_data["username"],
        name=sample_user_data["name"],
        password="oldpassword",
    )
    register(register_data, memory_repo)

    login_response = login(
        LoginRequest(username=sample_user_data["username"], password="oldpassword"),
        memory_repo,
    )

    # Change password
    change_password_data = ChangePasswordRequest(
        id=login_response.id,
        old_password="oldpassword",
        new_password="newpassword",
    )
    change_password(change_password_data, memory_repo)

    # Verify new password works
    login_response_new = login(
        LoginRequest(username=sample_user_data["username"], password="newpassword"),
        memory_repo,
    )

    assert login_response_new.username == sample_user_data["username"]


# ❌ Password change fails - wrong old password
def test_change_password_wrong_old(memory_repo, sample_user_data):
    """Test password change failure with wrong old password."""
    # Register user
    register_data = RegisterUser(
        username=sample_user_data["username"],
        name=sample_user_data["name"],
        password="correctpassword",
    )
    register(register_data, memory_repo)

    login_response = login(
        LoginRequest(username=sample_user_data["username"], password="correctpassword"),
        memory_repo,
    )

    # Try to change with wrong old password
    with pytest.raises(ValueError, match="Password lama salah"):
        change_password(
            ChangePasswordRequest(
                id=login_response.id,
                old_password="wrongoldpassword",
                new_password="newpassword",
            ),
            memory_repo,
        )


# 🌱 Admin user seeding (integrated with database initialization)
def test_admin_user_creation(memory_repo, admin_user_data):
    """Test admin user creation (simulating database initialization)."""
    # Create admin user directly (simulating database initialization)
    admin_user = User(
        username=admin_user_data["username"],
        name=admin_user_data["name"],
        password_hash=hash_password(admin_user_data["password"]),
        is_admin=True,
        is_active=True,
        # Let server_default handle timestamp
    )
    memory_repo.add_user(admin_user)

    # Verify admin user exists and can login
    admin_login = login(
        LoginRequest(
            username=admin_user_data["username"], password=admin_user_data["password"]
        ),
        memory_repo,
    )

    assert admin_login.username == admin_user_data["username"]

    # Verify admin user has admin privileges
    db_admin = memory_repo.get_by_username(admin_user_data["username"])
    assert db_admin.is_admin is True
    assert db_admin.is_active is True


# 🚫 Cannot deactivate admin user
def test_deactivate_user_only_non_admin(memory_repo, sample_user_data, admin_user_data):
    """Test that admin users cannot be deactivated."""
    # Create regular user
    register(
        RegisterUser(
            username=sample_user_data["username"],
            name=sample_user_data["name"],
            password=sample_user_data["password"],
        ),
        memory_repo,
    )

    # Create admin user
    admin_user = User(
        username=admin_user_data["username"],
        name=admin_user_data["name"],
        password_hash=hash_password(admin_user_data["password"]),
        is_admin=True,
        is_active=True,
    )
    memory_repo.add_user(admin_user)

    # Deactivate regular user should work
    regular_user = memory_repo.get_by_username(sample_user_data["username"])
    assert regular_user is not None
    deactivate_user(regular_user.id, memory_repo)

    # Verify user is deactivated
    deactivated_user = memory_repo.get_by_username(sample_user_data["username"])
    assert deactivated_user.is_active is False

    # Try to deactivate admin should fail
    admin_db_user = memory_repo.get_by_username(admin_user_data["username"])
    assert admin_db_user is not None

    with pytest.raises(ValueError, match="Tidak bisa nonaktifkan admin"):
        deactivate_user(admin_db_user.id, memory_repo)


# 🔄 Test user registration with duplicate username
def test_register_duplicate_username(memory_repo, sample_user_data):
    """Test registration failure with duplicate username."""
    # Register user first time
    register_data = RegisterUser(
        username=sample_user_data["username"],
        name=sample_user_data["name"],
        password=sample_user_data["password"],
    )
    register(register_data, memory_repo)

    # Try to register same username again
    with pytest.raises(ValueError, match="Username sudah digunakan"):
        register(register_data, memory_repo)


# 📊 Test repository operations directly
def test_repository_operations(memory_repo, sample_user_data):
    """Test repository CRUD operations."""
    # Create user
    user = User(
        username=sample_user_data["username"],
        name=sample_user_data["name"],
        password_hash=hash_password(sample_user_data["password"]),
        is_admin=False,
        is_active=True,
    )

    # Add user
    memory_repo.add_user(user)

    # Get by username
    retrieved_user = memory_repo.get_by_username(sample_user_data["username"])
    assert retrieved_user is not None
    assert retrieved_user.username == sample_user_data["username"]

    # Get by ID
    user_by_id = memory_repo.get_by_id(retrieved_user.id)
    assert user_by_id is not None
    assert user_by_id.username == sample_user_data["username"]

    # Update user
    retrieved_user.name = "Updated Name"
    memory_repo.update(retrieved_user)

    # Verify update
    updated_user = memory_repo.get_by_username(sample_user_data["username"])
    assert updated_user.name == "Updated Name"
