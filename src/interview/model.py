from pydantic import BaseModel


class ConversationRequest(BaseModel):
    ai: str
    user: str


class EditConversationRequest(BaseModel):
    user: str


class PatchInterviewViolation(BaseModel):
    violation: str
    description: str
