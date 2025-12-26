from fastapi import APIRouter, Depends


from src.authv1.model import PasswordResetRequest, UserV1Request
from src.shared.db import get_connection
from src.authv1.service import process_password_reset, process_user_info

route = APIRouter()


@route.post("/interview")
async def userinfo_route(request: UserV1Request, db=Depends(get_connection)):
    return await process_user_info(request, db)


@route.post("/reset-password")
async def reset_password_route(
    request: PasswordResetRequest, db=Depends(get_connection)
):
    user_id: int = 1
    return await process_password_reset(request, user_id, db)
