import os
from dotenv import load_dotenv
import jwt
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Header


from src.authv1.model import PasswordResetRequest, UserV1Request
from src.shared.db import get_connection
from src.authv1.service import process_password_reset, process_user_info

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