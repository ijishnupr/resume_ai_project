from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class ExchangeRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str


class UserV1Request(BaseModel):
    email: str
    interview_id: int
    job_description_id: int
    resume_id: int


class PasswordResetRequest(BaseModel):
    new_password: str
