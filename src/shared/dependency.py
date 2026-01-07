from uuid import UUID
import os

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

security = HTTPBearer()
load_dotenv()
JWT_SECRET: str = os.getenv("JWT_SECRET", "")


class UserPayload(BaseModel):
    """
    Data model representing the expected structure of the JWT payload.

    Attributes:
        user_id (UUID): The unique identifier of the authenticated user.
    Dev note:
        Used for scalability
    """

    user_id: UUID


async def has_access(
    request: Request, auth_creds: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Validates the JWT token and attaches the user payload to the request state.

    Args:
        request: The incoming HTTP request.
        auth_creds: The Bearer token credentials extracted from the header.

    Raises:
        HTTPException: If the token is invalid, expired, or malformed (401 Unauthorized).
    """

    try:
        payload = jwt.decode(
            auth_creds.credentials, key=JWT_SECRET, algorithms=["HS256"]
        )

        user = UserPayload(**payload)

        request.state.user = user

    except HTTPException as he:
        raise he
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
