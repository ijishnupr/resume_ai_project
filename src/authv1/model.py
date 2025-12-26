from pydantic import BaseModel


class UserV1Request(BaseModel):
    email: str
    interview_id: int
    job_description_id: int
    resume_id: int


class PasswordResetRequest(BaseModel):
    new_password: str
