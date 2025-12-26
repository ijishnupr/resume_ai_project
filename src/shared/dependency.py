from dotenv import load_dotenv
import os
from pydantic import BaseModel
import jwt
from datetime import datetime
from requests import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, Request, HTTPException, status

security = HTTPBearer()
load_dotenv()
JWT_SECRET: str = os.getenv("JWT_SECRET", "")



class UserPayload(BaseModel):
    user_code: str
    user_id: int
    exp: datetime

async def has_access(
    request: Request, auth_creds: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        
        payload = jwt.decode(
            auth_creds.credentials, 
            key=JWT_SECRET, 
            algorithms=["HS256"]
        )
        
        user = UserPayload(**payload)

      
        if user.exp < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.user = user

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
