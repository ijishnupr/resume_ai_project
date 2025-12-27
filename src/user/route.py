from fastapi import APIRouter, Depends, Request

from src.shared.db import get_connection
from src.shared.dependency import has_access
from src.user.service import me

route = APIRouter()
PROTECTED = [Depends(has_access)]


@route.get("/", dependencies=PROTECTED)
async def me_route(request: Request, db=Depends(get_connection)):
    return await me(request.state.user, db)
