import jwt
from typing import Annotated
import os
from dotenv import load_dotenv
from click.decorators import R

from fastapi import APIRouter, Depends, Header, HTTPException, status
from src.auth.model import (
    ExchangeRequest,
    LoginRequest,
    PasswordResetRequest,
    UserV1Request,
)
from src.auth.service import (
    process_password_reset,
    process_user_info,
    user_login,
    exchange,
)
from src.shared.db import get_connection

# only use this auth for admin
route = APIRouter()


load_dotenv()
JWT_SECRET_EMAIL: str = os.getenv("JWT_SECRET_EMAIL", "")


@route.post("/interview")
async def userinfo_route(request: UserV1Request, db=Depends(get_connection)):
    return await process_user_info(request, db)



@route.post("/reset-password")
async def reset_password_route(
    request: PasswordResetRequest,
    x_token: Annotated[str, Header()], 
    db = Depends(get_connection)
):
    try:
        payload = jwt.decode(
            x_token, 
            key=JWT_SECRET_EMAIL, 
            algorithms=["HS256"]
        )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise Exception("Token payload invalid")

        

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Reset token has expired",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token",
        )
    return await process_password_reset(request, user_id, db)

# return refresh token
@route.post("/login")
async def login_route(request: LoginRequest, db=Depends(get_connection)):
    return await user_login(request, db)


@route.post("/exchange")
async def exchange_route(request: ExchangeRequest, db=Depends(get_connection)):
    return await exchange(request, db)


