import json
from fastapi import Request
from pydantic import JsonValue
import os
from dotenv import load_dotenv
import secrets
from src.auth.model import (
    ExchangeRequest,
    LoginRequest,
    PasswordResetRequest,
    UserV1Request,
)
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

load_dotenv()
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_SECRET_EMAIL: str = os.getenv("JWT_SECRET_EMAIL", "")


async def process_user_info(job_requisition_id:int,request: UserV1Request, db):
    conn, cur = db
    for resume_id in request.resume_ids:
        get_user_email_query = """
        SELECT 
            cu.email 
        FROM
            candidate_user cu
        JOIN 
            resume_detail rd ON rd.candidate_user_id = cu.id
        where 
            rd.id = %(resume_id)s
        """
        await cur.execute(get_user_email_query,{"resume_id":resume_id})
        user_email = await cur.fetchone()
        user_email = user_email["email"]
        get_user_query = """
        SELECT 
            id 
        FROM 
            app_user 
        WHERE 
            email = %(email)s
        """
        await cur.execute(get_user_query, {"email": user_email})
        user_record = await cur.fetchone()

        user_id = None
        is_password_reset = False
        if user_record:
            user_id = user_record["id"]
            is_password_reset = True

        else:
            insert_user_query = """
            INSERT INTO app_user 
                ( email)
            VALUES 
                ( %(email)s)
            RETURNING id
            """
            await cur.execute(
                insert_user_query,
                {
                    "email": user_email,
                },
            )
            new_user = await cur.fetchone()
            user_id = new_user["id"]
            ph = PasswordHasher()
            # random_password: str = secrets.token_urlsafe(12)
            random_password: str = "password"
            encoded_password: str = ph.hash(random_password)

            insert_into_temp_password_query = """
            UPDATE
                app_user
            SET
                password = %(temp_password)s
            WHERE
                id = %(user_id)s
            """
            await cur.execute(
                insert_into_temp_password_query,
                {"temp_password": encoded_password, "user_id": user_id},
            )

        insert_interview_query = """
        INSERT INTO 
            interview 
            (user_id, job_requisition_id,resume_id)
        VALUES 
            (%(user_id)s,  %(job_requisition_id)s, %(resume_id)s)
        RETURNING id
        """
        await cur.execute(
            insert_interview_query,
            {
                "user_id": user_id,
                "job_requisition_id": job_requisition_id,
                "resume_id": resume_id,
            },
        )
        interview_record = await cur.fetchone()
        interview_id = interview_record["id"]

        
        insert_status_query = """
        INSERT INTO interview_status 
            (interview_id, status)
        VALUES 
            (%(interview_id)s, 'SCHEDULED')
        """
        await cur.execute(insert_status_query, {"interview_id": interview_id})

        # send_email_functionality_here
        if is_password_reset:
            # send mail for existion user
            pass
        else:
            # send mail for new user
            pass

    return {
        "message": "User processed and interview generated",
        
    }


async def process_password_reset(request: PasswordResetRequest, user_id: int, db):
    conn, cur = db
    ph = PasswordHasher()

    encoded_password: str = ph.hash(request.new_password)
    check_password_reset_available_query = """
    SELECT
        id
    FROM
        app_user 
    WHERE
        id = %(user_id)s and is_reset_password = FALSE
    """
    await cur.execute(check_password_reset_available_query, {"user_id": user_id})
    user_data = await cur.fetchone()
    if not user_data:
        return {"Password is already changed"}
    insert_into_app_user_query = """
    UPDATE
        app_user
    SET
        password = %(new_password)s, is_reset_password = TRUE
    WHERE
        id = %(user_id)s 
    """
    await cur.execute(
        insert_into_app_user_query,
        {"new_password": encoded_password, "user_id": user_id},
    )
    return {
        "message": "Password reset processed",
    }


async def user_login(client_req:Request,request: LoginRequest, db):
    conn, cur = db
    get_user_query = """
    SELECT
        email,
        password,
        id as user_id,
        is_reset_password
    FROM
        app_user
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
    ip_address = client_req.headers.get("x-forwarded-for", client_req.client.host).split(",")[0]
    user_agent = client_req.headers.get("user-agent")
    
    metadata = {
        "browser": user_agent, 
        "platform": client_req.headers.get("sec-ch-ua-platform", "unknown"),
    }
    insert_session_query = """
    INSERT INTO user_sessions 
        (user_id, refresh_token, ip_address, user_agent, metadata)
    VALUES 
        (%(user_id)s, %(token)s, %(ip)s, %(ua)s, %(meta)s)
    """
    await cur.execute(
        insert_session_query, 
        {
            "user_id": user_record["user_id"], 
            "token": refresh_token,
            "ip": ip_address,
            "ua": user_agent,
            "meta": json.dumps(metadata) 
        }
    )

    access_token = await exchange(refresh_token,db)
    response= {"refresh_token": refresh_token, "is_reset_password": True}
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
        ut.token = %(token)s
    """
    await cur.execute(get_token_query, {"token": refresh_token})
    token_record = await cur.fetchone()
    if not token_record:
        return {"error": "Invalid refresh token"}
    data = {"user_id": token_record["user_id"]}

    encoded_jwt = jwt.encode(data, JWT_SECRET, algorithm="HS256")
    return {"access_token":encoded_jwt}
