from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterUserRequest(BaseModel):
    username: str
    name: str
    password: str
    is_admin: bool = False
    is_active: bool = True


class AddUserRequest(BaseModel):
    username: str
    name: str
    password: str
    is_admin: bool = False
    is_active: bool = True


class ChangePasswordRequest(BaseModel):
    id: int
    old_password: str
    new_password: str


class ChangeNameRequest(BaseModel):
    id: int
    new_name: str
