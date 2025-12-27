from argon2 import PasswordHasher
from fastapi import status
from fastapi.responses import JSONResponse

from src.interview.model import UserV1Request
from src.shared.dependency import UserPayload


async def process_user_info(job_requisition_id: int, request: UserV1Request, db):
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
        await cur.execute(get_user_email_query, {"resume_id": resume_id})
        user_email = await cur.fetchone()
        user_email = user_email["email"]
        get_user_query = """
        SELECT
            id
        FROM
            interview_candidate
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
            INSERT INTO interview_candidate
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
                interview_candidate
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


async def list_interview(user: UserPayload, db):
    conn, cur = db

    get_interview_query = """
    SELECT
        i.created_at,ins.status,jr.name as title,'Ylogx' as company_name,i.id,'PRESCREENING' as interview_type
    FROM
        interview i
    JOIN
        interview_status ins ON ins.interview_id = i.id and end_time = '2100-01-01 00:00:00+00'
    JOIN
        job_requisition jr ON jr.id = i.job_requisition_id
    WHERE user_id = %(user_id)s
    """
    await cur.execute(get_interview_query, {"user_id": user.user_id})
    interviews = await cur.fetchall()

    return interviews


async def interview_route(interview_id: int, user: UserPayload, db):
    conn, cur = db

    get_interview_query = """
    SELECT
        i.created_at,ins.status,jr.name as title,'Ylogx' as company_name,i.id,'PRESCREENING' as interview_type
    FROM
        interview i
    JOIN
        interview_status ins ON ins.interview_id = i.id and end_time = '2100-01-01 00:00:00+00'
    JOIN
        job_requisition jr ON jr.id = i.job_requisition_id
    WHERE i.id = %(interview_id)s
    """
    await cur.execute(get_interview_query, {"interview_id": interview_id})
    interview = await cur.fetchone()
    if not interview:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )

    return interview
