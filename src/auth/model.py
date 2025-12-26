from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class ExchangeRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str

class UserInfoRequest(BaseModel):
    user_code: str
    password_hash: str | None = None
    full_name: str | None = None
    email: str | None = None