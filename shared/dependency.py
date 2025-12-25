from pydantic import BaseModel
import jwt
from datetime import datetime
from requests import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import Depends, Request

security = HTTPBearer()

class UserPayload(BaseModel):
    user_code: str
    user_id: int
    expiry: datetime
    

async def has_access(request:Request, auth_creds:HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            auth_creds.credentials,key = "your_secret_key", algorithms=["HS256"]
        )
        user = UserPayload(**payload)
        if user.expiry < datetime.now():
            raise Exception("Token has expired")
        request.state.user = user
    except Exception as e:
        raise Exception("Invalid token") from e 
    
    