from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class ExchangeRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str
