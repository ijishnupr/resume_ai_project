import os
from dotenv import load_dotenv
import secrets
from src.auth.model import ExchangeRequest, LoginRequest, PasswordResetRequest, UserV1Request
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

load_dotenv()
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_SECRET_EMAIL: str = os.getenv("JWT_SECRET_EMAIL", "")




async def process_user_info(request: UserV1Request, db):
    conn, cur = db

    get_user_query = """
    SELECT 
        id 
    FROM 
        app_user 
    WHERE 
        email = %(email)s
    """
    await cur.execute(get_user_query, {"email": request.email})
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
                "email": request.email,
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
        (user_id, interview_code, job_description_id,resume_id)
    VALUES 
        (%(user_id)s, %(interview_code)s, %(job_description_id)s, %(resume_id)s)
    RETURNING id
    """
    await cur.execute(
        insert_interview_query,
        {
            "user_id": user_id,
            "interview_code": request.interview_id,
            "job_description_id": request.job_description_id,
            "resume_id": request.resume_id,
        },
    )
    interview_record = await cur.fetchone()
    interview_id = interview_record["id"]

    interview_code = request.interview_id
    update_code_query = """
    UPDATE 
        interview
    SET 
        interview_code = %(interview_code)s
    WHERE 
        id = %(id)s
    """
    await cur.execute(
        update_code_query, {"interview_code": interview_code, "id": interview_id}
    )

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
        "user_id": user_id,
        "interview_id": interview_id,
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
    await cur.execute(
        check_password_reset_available_query,{"user_id":user_id}
    )
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


async def user_login(request: LoginRequest, db):
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
    return {"refresh_token": refresh_token, "is_reset_password": True}


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

    encoded_jwt = jwt.encode(data, JWT_SECRET, algorithm="HS256")
    return encoded_jwt

