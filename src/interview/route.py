from fastapi import APIRouter, Depends, Request

from src.interview.model import (
    ConversationRequest,
    EditConversationRequest,
    PatchInterviewViolation,
)
from src.interview.service import (
    edit_conversation,
    get_conversation,
    insert_conversation,
    interview_detail,
    list_interview,
    start_interview,
    update_interview_status,
    update_interview_violation,
)
from src.shared.db import get_connection
from src.shared.dependency import has_access

route = APIRouter()
PROTECTED = [Depends(has_access)]


@route.get("/", dependencies=PROTECTED)
async def interview_list_route(request: Request, db=Depends(get_connection)):
    return await list_interview(request.state.user, db)


@route.get("/{interview_id}", dependencies=PROTECTED)
async def interview_detail_route(
    interview_id: str, request: Request, db=Depends(get_connection)
):
    return await interview_detail(interview_id, request.state.user, db)


@route.get("/{interview_id}/start", dependencies=PROTECTED)
async def start_interview_route(
    interview_id: str, request: Request, db=Depends(get_connection)
):
    return await start_interview(interview_id, request.state.user, db)


@route.post("/{interview_id}/conversation", dependencies=PROTECTED)
async def insert_conversation_route(
    interview_id: str,
    request: ConversationRequest,
    db=Depends(
        get_connection,
    ),
):
    return await insert_conversation(interview_id, request, db)


@route.post("/{interview_id}/close", dependencies=PROTECTED)
async def update_interview_status_route(interview_id: int, db=Depends(get_connection)):
    return await update_interview_status(interview_id, "SESSION_CLOSED", db)


@route.post("/{interview_id}/completed", dependencies=PROTECTED)
async def update_interview_status_complete_route(
    interview_id: int, db=Depends(get_connection)
):
    return await update_interview_status(interview_id, "COMPLETED", db)


@route.get("/{interview_id}/conversation", dependencies=PROTECTED)
async def get_conversation_route(interview_id: str, db=Depends(get_connection)):
    return await get_conversation(interview_id, db)


@route.post("/conversation/{conversation_id}", dependencies=PROTECTED)
async def edit_conversation_route(
    conversation_id: int, request: EditConversationRequest, db=Depends(get_connection)
):
    return await edit_conversation(conversation_id, request.conversation, db)


@route.post("/{interview_id}/violation")
async def update_interview_violation_route(
    interview_id: str, request: PatchInterviewViolation, db=Depends(get_connection)
):
    return await update_interview_violation(interview_id, request, db)
