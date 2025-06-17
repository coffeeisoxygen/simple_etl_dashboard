from pydantic import BaseModel, ConfigDict


class LoginResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    is_admin: bool
    is_active: bool


class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    is_admin: bool
    is_active: bool
