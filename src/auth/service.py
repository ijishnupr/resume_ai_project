import json
import os
import secrets

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from fastapi import Request

from src.auth.model import (
    LoginRequest,
    PasswordResetRequest,
)

load_dotenv()
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_SECRET_EMAIL: str = os.getenv("JWT_SECRET", "")


async def process_password_reset(request: PasswordResetRequest, user_id: int, db):
    conn, cur = db
    ph = PasswordHasher()

    encoded_password: str = ph.hash(request.new_password)
    check_password_reset_available_query = """
    SELECT
        id
    FROM
        candidate_user
    WHERE
        id = %(user_id)s and is_reset_password = FALSE
    """
    await cur.execute(check_password_reset_available_query, {"user_id": user_id})
    user_data = await cur.fetchone()
    if not user_data:
        return {"Password is already changed"}
    insert_into_interview_candidate_query = """
    UPDATE
        candidate_user
    SET
        password = %(new_password)s, is_reset_password = TRUE
    WHERE
        id = %(user_id)s
    """
    await cur.execute(
        insert_into_interview_candidate_query,
        {"new_password": encoded_password, "user_id": user_id},
    )
    return {
        "message": "Password reset processed",
    }


async def user_login(client_req: Request, request: LoginRequest, db):
    conn, cur = db
    get_user_query = """
    SELECT
        email,
        password,
        id as user_id,
        is_reset_password
    FROM
        candidate_user
    WHERE
        email = %(email)s
    """
    await cur.execute(get_user_query, {"email": request.username})
    user_record = await cur.fetchone()
    if not user_record:
        return {"error": "Invalid usercode"}

    password = user_record["password"]
    ph = PasswordHasher()
    try:
        ph.verify(password, request.password)
    except VerifyMismatchError:
        return {"error": "Invalid password"}

    if not user_record["is_reset_password"]:
        data = {"user_id": user_record["user_id"]}
        encoded_jwt = jwt.encode(data, JWT_SECRET_EMAIL, algorithm="HS256")
        return {"is_reset_password": False, "token": encoded_jwt}
    refresh_token = secrets.token_urlsafe(64)
    ip_address = client_req.headers.get(
        "x-forwarded-for", client_req.client.host
    ).split(",")[0]
    user_agent = client_req.headers.get("user-agent")

    metadata = {
        "browser": user_agent,
        "platform": client_req.headers.get("sec-ch-ua-platform", "unknown"),
    }
    insert_session_query = """
    INSERT INTO user_session
        (user_id, refresh_token)
    VALUES
        (%(user_id)s, %(token)s)
    """
    await cur.execute(
        insert_session_query,
        {
            "user_id": user_record["user_id"],
            "token": refresh_token,
            "ip": ip_address,
            "ua": user_agent,
            "meta": json.dumps(metadata),
        },
    )

    access_token = await exchange(refresh_token, db)
    response = {"refresh_token": refresh_token, "is_reset_password": True}
    response.update(access_token)
    return response


async def exchange(refresh_token: str, db):
    conn, cur = db
    get_token_query = """
    SELECT
        ut.user_id
    FROM
        user_session ut

    WHERE
        ut.refresh_token = %(token)s
    """
    await cur.execute(get_token_query, {"token": refresh_token})
    token_record = await cur.fetchone()
    if not token_record:
        return {"error": "Invalid refresh token"}
    data = {"user_id": token_record["user_id"]}

    encoded_jwt = jwt.encode(data, JWT_SECRET, algorithm="HS256")
    return {"access_token": encoded_jwt}
