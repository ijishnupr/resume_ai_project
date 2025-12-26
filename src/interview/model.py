from pydantic import BaseModel


class UserV1Request(BaseModel):
    resume_ids: list[int]
