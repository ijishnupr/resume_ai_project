import jwt
from typing import Annotated
from fastapi.openapi.models import Header
from fastapi import APIRouter, Depends, HTTPException, status


from auth.service import JWT_SECRET_EMAIL
from src.authv1.model import PasswordResetRequest, UserV1Request
from src.shared.db import get_connection
from src.authv1.service import process_password_reset, process_user_info

route = APIRouter()


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
        # 1. Manually decode the token using the specific email secret
        payload = jwt.decode(
            x_token, 
            key=JWT_SECRET_EMAIL, 
            algorithms=["HS256"]
        )
        
        # 2. Extract user_id
        user_id = payload.get("user_id")
        if not user_id:
            raise Exception("Token payload invalid")

        # 3. Call your service function
        return await process_password_reset(request, user_id, db)

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