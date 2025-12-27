from fastapi import APIRouter, Depends, Request

from src.interview.model import UserV1Request
from src.interview.service import (
    interview_route,
    list_interview,
    process_user_info,
    start_interview,
)
from src.shared.db import get_connection
from src.shared.dependency import has_access

route = APIRouter()
PROTECTED = [Depends(has_access)]


@route.post("/{job_requisition_id}")
async def userinfo_route(
    job_requisition_id: int, request: UserV1Request, db=Depends(get_connection)
):
    return await process_user_info(job_requisition_id, request, db)


@route.get("/", dependencies=PROTECTED)
async def interview_list_route(request: Request, db=Depends(get_connection)):
    return await list_interview(request.state.user, db)


@route.get("/{interview_id}", dependencies=PROTECTED)
async def interview_detail_route(
    interview_id: int, request: Request, db=Depends(get_connection)
):
    return await interview_route(interview_id, request.state.user, db)


@route.get("/start/{interview_id}", dependencies=PROTECTED)
async def start_interview_route(
    interview_id: int, request: Request, db=Depends(get_connection)
):
    return await start_interview(interview_id, request.state.user, db)
