import dbm.dumb

from fastapi import APIRouter, Depends, Request

from src.interview.service import list_interview
from src.shared.db import get_connection


route = APIRouter()


@route.get("/")
async def interview_list_route(request:Request,db=Depends(get_connection)):
    return list_interview(request.state.user,db)