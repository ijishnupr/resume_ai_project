from click.decorators import R

from fastapi import APIRouter, Depends
from auth.model import (
    ExchangeRequest,
    LoginRequest,
    PatchUserRequest,
    ResetPasswordRequest,
)
from auth.service import request_reset_password, reset_password, user_login, exchange
import router
from shared.db import get_connection

# only use this auth for admin
route = APIRouter()


# return refresh token
@route.get("/login")
async def login_route(request: LoginRequest, db=Depends(get_connection)):
    return await user_login(request, db)


@route.get("/exchange")
async def exchange_route(request: ExchangeRequest, db=Depends(get_connection)):
    return await exchange(request, db)


@route.post("/userinfo")
async def userinfo_route(request: PatchUserRequest, db=Depends(get_connection)):
    return {"message": "User info endpoint"}


@route.get("{user_code}/reset-password")
async def reset_password_request_route(user_code: str, db=Depends(get_connection)):
    return await request_reset_password(user_code, db)


@route.post("/reset-password")
async def reset_password_route(
    request: ResetPasswordRequest, db=Depends(get_connection)
):
    return await reset_password(request.reset_token, request.new_password, db)
