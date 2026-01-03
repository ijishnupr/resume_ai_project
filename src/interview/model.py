from typing import Literal

from pydantic import BaseModel


class ConversationRequest(BaseModel):
    conversation: str
    source: Literal["AI", "USER"]


class EditConversationRequest(BaseModel):
    conversation: str


class PatchInterviewViolation(BaseModel):
    violation: str
    description: str
