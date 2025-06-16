"""module for authentication schemas."""

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    """Login request schema."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int  # 🔧 FIXED: Match database field name
    username: str
    name: str


class RegisterUser(BaseModel):
    """Register user schema."""

    username: str
    name: str
    password: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""

    id: int  # 🔧 FIXED: Match database field name
    old_password: str
    new_password: str
