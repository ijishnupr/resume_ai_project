import os
from dotenv import load_dotenv
from asyncio import exceptions
from datetime import datetime, timedelta
import secrets
from src.auth.model import ExchangeRequest, LoginRequest
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

load_dotenv()
JWT_SECRET: str = os.getenv("JWT_SECRET", "")


async def user_login(request: LoginRequest, db):
    conn, cur = db
    get_user_query = """
    SELECT
        user_code,
        password,
        id as user_id
    FROM
        app_user
    WHERE
        user_code = %(user_code)s
    """
    await cur.execute(get_user_query, {"user_code": request.username})
    user_record = await cur.fetchone()
    if not user_record:
        return {"error": "Invalid usercode"}
    password = user_record["password"]
    ph = PasswordHasher()
    try:
        ph.verify(password, request.password)
    except VerifyMismatchError:
        return {"error": "Invalid password"}

    refresh_token = secrets.token_urlsafe(64)
    insert_token_query = """
    INSERT INTO 
        user_token 
            (user_id, token)
    VALUES 
        (%(user_id)s, %(token)s)
    ON CONFLICT(user_id) 
        DO UPDATE SET token = %(token)s
    """
    await cur.execute(
        insert_token_query, {"user_id": user_record["user_id"], "token": refresh_token}
    )
    return {"refresh_token": refresh_token}


async def exchange(request: ExchangeRequest, db):
    conn, cur = db
    get_token_query = """
    SELECT
        ut.user_id
    FROM
        user_token ut
    
    WHERE
        ut.token = %(token)s
    """
    await cur.execute(get_token_query, {"token": request.refresh_token})
    token_record = await cur.fetchone()
    if not token_record:
        return {"error": "Invalid refresh token"}
    data = {"user_id": token_record["user_id"]}
    expire = datetime.now() + timedelta(minutes=30)
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, JWT_SECRET, algorithm="HS256")
    return encoded_jwt


async def request_reset_password(user_code: str, db):
    conn, cur = db

    get_user_query = """
    SELECT 
        id 
    FROM
        app_user 
    WHERE 
        user_code = %(user_code)s
    """
    await cur.execute(get_user_query, {"user_code": user_code})
    user = await cur.fetchone()

    if not user:
        return {"message": "User not found"}

    reset_token = secrets.token_urlsafe(48)
    expires_at = datetime.now() + timedelta(minutes=15)

    insert_query = """
    INSERT INTO
        password_reset_token (user_id, token, expires_at)
    VALUES 
        (%(user_id)s, %(token)s, %(expires_at)s)
    ON CONFLICT 
        (user_id)
    DO UPDATE 
        SET token = %(token)s, expires_at = %(expires_at)s
    """
    await cur.execute(
        insert_query,
        {"user_id": user["id"], "token": reset_token, "expires_at": expires_at},
    )

    # send temporary reset token
    return {"message": "Password reset token generated, check your email."}


async def reset_password(token: str, new_password: str, db):
    conn, cur = db

    get_token_query = """
    SELECT 
        user_id, expires_at
    FROM 
        password_reset_token
    WHERE 
        token = %(token)s
    """
    await cur.execute(get_token_query, {"token": token})
    record = await cur.fetchone()

    if not record:
        return {"error": "Invalid or expired token"}

    if record["expires_at"] < datetime.now():
        return {"error": "Token expired"}

    ph = PasswordHasher()
    hashed_password = ph.hash(new_password)

    update_password_query = """
    UPDATE 
        app_user
    SET password = %(password)s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %(user_id)s
    """
    await cur.execute(
        update_password_query,
        {"password": hashed_password, "user_id": record["user_id"]},
    )

    return {"message": "Password reset successful"}
