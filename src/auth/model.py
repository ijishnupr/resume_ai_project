from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class ExchangeRequest(BaseModel):
    refresh_token: str


class PatchUserRequest(BaseModel):
    full_name: str | None = None
    email: str | None = None
    password: str | None = None


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
