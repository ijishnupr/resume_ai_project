
from asyncio import exceptions
from datetime import datetime, timedelta
from auth.model import LoginRequest
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


async def user_login(request:LoginRequest, db):
    conn,cur = db
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
    password = user_record['password']
    ph = PasswordHasher()
    try:
        ph.verify(password, request.password)
    except VerifyMismatchError:
        return {"error": "Invalid password"}
    
    expire = datetime.now() + timedelta(hours=24)
    payload = {
        "user_code": request.username,
        "user_id": user_record['user_id'],
        "exp": expire
    }
    token = jwt.encode(payload, "asdfas", algorithm="HS256")
    return {"token": token}
  