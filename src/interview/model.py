from typing import Literal

from pydantic import BaseModel


class UserV1Request(BaseModel):
    resume_ids: list[int]


class ConversationRequest(BaseModel):
    conversation: str
    source: Literal["AI", "USER"]
