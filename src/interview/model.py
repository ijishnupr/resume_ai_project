from pydantic import BaseModel


class ConversationRequest(BaseModel):
    ai: str
    user: str


class EditConversationRequest(BaseModel):
    conversation: str


class PatchInterviewViolation(BaseModel):
    violation: str
    description: str
