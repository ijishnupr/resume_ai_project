from click.decorators import R

from fastapi import APIRouter, Depends
from src.auth.model import (
    ExchangeRequest,
    LoginRequest,
    ResetPasswordRequest,
    UserInfoRequest,
)
from src.auth.service import process_user_info, request_reset_password, reset_password, user_login, exchange
from src.shared.db import get_connection

# only use this auth for admin
route = APIRouter()


# return refresh token
@route.get("/login")
async def login_route(request: LoginRequest, db=Depends(get_connection)):
    return await user_login(request, db)


@route.post("/exchange")
async def exchange_route(request: ExchangeRequest, db=Depends(get_connection)):
    return await exchange(request, db)


@route.post("/userinfo")
async def userinfo_route(request: UserInfoRequest, db=Depends(get_connection)):
    return await process_user_info(request, db)


@route.get("/{user_code}/reset-password")
async def reset_password_request_route(user_code: str, db=Depends(get_connection)):
    return await request_reset_password(user_code, db)


@route.post("/reset-password")
async def reset_password_route(
    request: ResetPasswordRequest, db=Depends(get_connection)
):
    return await reset_password(request.reset_token, request.new_password, db)

