import os
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from src.auth.model import (
    ExchangeRequest,
    LoginRequest,
    PasswordResetRequest,
)
from src.auth.service import (
    exchange,
    process_password_reset,
    user_login,
)
from src.shared.db import get_connection

# only use this auth for admin
route = APIRouter()


load_dotenv()
JWT_SECRET_EMAIL: str = os.getenv("JWT_SECRET_EMAIL", "")


@route.post("/reset-password")
async def reset_password_route(
    request: PasswordResetRequest,
    x_token: Annotated[str, Header()],
    db=Depends(get_connection),
):
    try:
        payload = jwt.decode(x_token, key=JWT_SECRET_EMAIL, algorithms=["HS256"])

        user_id = payload.get("user_id")
        if not user_id:
            raise Exception("Token payload invalid")

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token has expired",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token",
        )
    return await process_password_reset(request, user_id, db)


# return refresh token
@route.post("/login")
async def login_route(
    client_request: Request, request: LoginRequest, db=Depends(get_connection)
):
    return await user_login(client_request, request, db)


@route.post("/exchange")
async def exchange_route(request: ExchangeRequest, db=Depends(get_connection)):
    return await exchange(request.refresh_token, db)
