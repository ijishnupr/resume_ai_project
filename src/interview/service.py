import os

import httpx
from argon2 import PasswordHasher
from dotenv import load_dotenv
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from src.interview.model import ConversationRequest, UserV1Request
from src.interview.prompts import InstructionType, get_base_instructions
from src.shared.dependency import UserPayload

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


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
        ciqs.created_at,
        ciqs.status,
        jd.job_title AS title,
        'Ylogx' AS company_name,
        ciqs.id,
        UPPER(ciqs.interview_mode) AS interview_type
    FROM
        candidate_interview_question_session ciqs
    JOIN
        job_requisition jr ON ciqs.job_requisition_id = jr.id
    JOIN
        job_description jd ON jr.job_description_id = jd.id
    WHERE
        ciqs.resume_detail_id = %(user_id)s
    """

    await cur.execute(get_interview_query, {"user_id": user.user_id})
    interviews = await cur.fetchall()

    return interviews


async def interview_detail(interview_id: str, user: UserPayload, db):
    conn, cur = db

    get_interview_query = """
    SELECT
        ciqs.created_at,
        ciqs.status,
        jd.job_title AS title,
        'Ylogx' AS company_name,
        ciqs.id,
        UPPER(ciqs.interview_mode) AS interview_type
    FROM
        candidate_interview_question_session ciqs
    JOIN
        job_requisition jr ON ciqs.job_requisition_id = jr.id
    JOIN
        job_description jd ON jr.job_description_id = jd.id
    WHERE
        ciqs.id = %(interview_id)s
    """
    await cur.execute(get_interview_query, {"interview_id": interview_id})
    interview = await cur.fetchone()
    if not interview:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )

    return interview


async def get_interview_details(interview_id: str, db):
    conn, cur = db

    get_interview_query = """
    SELECT
        -- Basic Session Info
        ciqs.id,
        ciqs.created_at,
        ciqs.status,
        UPPER(ciqs.interview_mode) AS interview_type,
        'Ylogx' AS company_name,

        jd.job_title,
        jd.job_description,
        jd.responsibilities,
        jd.must_have_skills,
        jd.nice_to_have_skills,

        -- Resume Data (For {candidate_resume})
        jsonb_build_object(
            'name', rd.name,
            'raw_text', rd.cf_text,
            'skills', rd.skill_set,
            'experience', rd.work_experience,
            'details', rd.details
        ) as candidate_resume,

        -- Technical L1 Questions (JSONB columns from schema)
        ct.technical_questions,
        ct.recruiter_added_questions AS technical_custom_questions,

        -- Prescreening Questions (Aggregated into a JSON list)
        (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'question_text', cqp.question_text,
                    'preferred_answer', cqp.preferred_answer,
                    'created_by', cqp.created_by,
                    'is_mandatory', cqp.is_mandatory
                )
            )
            FROM candidate_question_prescreening cqp
            WHERE cqp.job_requisition_id = ciqs.job_requisition_id
        ) AS prescreen_questions

    FROM
        candidate_interview_question_session ciqs
    -- Join Job Description directly via the session ID
    LEFT JOIN
        job_description jd ON ciqs.job_description_id = jd.id
    -- Join Resume Detail
    LEFT JOIN
        resume_detail rd ON ciqs.resume_detail_id = rd.id
    -- Join Technical Questions (Linked via Requisition ID)
    LEFT JOIN
        candidate_technical_L1_question ct ON ct.job_requisition_id = ciqs.job_requisition_id
    WHERE
        ciqs.id = %(interview_id)s
    """

    await cur.execute(get_interview_query, {"interview_id": interview_id})
    interview_data = await cur.fetchone()

    return interview_data


async def get_ephemeral_token(interview: dict):
    async with httpx.AsyncClient() as client:
        job_title = interview["job_title"]
        job_description = interview["job_description"]
        candidate_resume = interview["candidate_resume"]
        # generated_questions_section = interview["generated_questions_section"]
        # custom_questions_section = interview["custom_questions_section"]
        instructions = get_base_instructions(
            InstructionType("PRESCREENING"),
            job_title,
            candidate_resume,
            job_description,
            "None",
            "None",
        )
        response = await client.post(
            "https://api.openai.com/v1/realtime/sessions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-realtime-preview-2024-12-17",
                "voice": "alloy",
                "instructions": instructions,
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="Failed to create session"
            )

        return response.json()


async def start_interview(interview_id: str, user: UserPayload, db):
    conn, cur = db
    interview = await get_interview_details(interview_id, db)
    if interview and interview["status"] != "pending":
        return {"message": "Token Already generated"}
    token = await get_ephemeral_token(interview)
    insert_into_interview_query = """
    UPDATE
        candidate_interview_question_session
    SET
     status = 'in_progress'
    WHERE
        id = %(interview_id)s
    """

    await cur.execute(
        insert_into_interview_query,
        {"interview_id": interview_id},
    )

    # Need this code if status history is required

    # update_interview_status_query = """
    # UPDATE
    #     interview_status
    # SET
    #     end_time = now()
    # WHERE
    #     interview_id = %(interview_id)s and end_time = '2100-01-01 00:00:00+00'
    # """
    # await cur.execute(update_interview_status_query, {"interview_id": interview_id})
    # insert_interview_status = """
    # INSERT INTO
    #     interview_status
    #     (interview_id,status)
    # VALUES
    #     (%(interview_id)s,'ACTIVE')

    # """
    # await cur.execute(insert_interview_status, {"interview_id": interview_id})

    return token["client_secret"]


async def insert_conversation(interview_id, request: ConversationRequest, db):
    conn, cur = db
    check_interview_available_query = """
    SELECT
        id
    FROM
        interview
    WHERE
        id = %(interview_id)s
    """
    await cur.execute(check_interview_available_query, {"interview_id": interview_id})
    interview = await cur.fetchone()
    if not interview:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )
    insert_into_interview_conversation_query = """
    INSERT INTO
        interview_conversation
        (interview_id,transcript_data,type)
    VALUES
        (%(interview_id)s,%(transcript_data)s,%(type)s)
    """
    await cur.execute(
        insert_into_interview_conversation_query,
        {
            "interview_id": interview_id,
            "transcript_data": request.conversation,
            "type": request.source,
        },
    )
    return {"message": "Conversation Updated"}


async def update_interview_status(interview_id: int, interview_status: str, db):
    conn, cur = db
    check_interview_available_query = """
    SELECT
        i.id,ins.status
    FROM
        interview i
    JOIN
        interview_status ins ON ins.interview_id = i.id and end_time = '2100-01-01 00:00:00+00'
    WHERE
        i.id = %(interview_id)s
    """
    await cur.execute(check_interview_available_query, {"interview_id": interview_id})
    interview = await cur.fetchone()
    if not interview:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )
    previous_status = interview["status"]
    if previous_status == "ACTIVE":
        update_interview_status_query = """
        UPDATE
            interview_status
        SET
            end_time = now()
        WHERE
            interview_id = %(interview_id)s and end_time = '2100-01-01 00:00:00+00'
        """
        await cur.execute(update_interview_status_query, {"interview_id": interview_id})
        insert_interview_status = """
        INSERT INTO
            interview_status
            (interview_id,status)
        VALUES
            (%(interview_id)s,%(status)s)

        """
        await cur.execute(
            insert_interview_status,
            {"interview_id": interview_id, "status": interview_status},
        )

        return {"message": "Interview Status Updated"}

    elif previous_status == "CLOSED":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Session Is Already Closed"},
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Session Is Already COMPLETED"},
        )


async def get_conversation(interview_id: int, db):
    conn, cur = db
    check_interview_available_query = """
    SELECT
        i.id
    FROM
        interview i
    WHERE
        i.id = %(interview_id)s
    """
    await cur.execute(check_interview_available_query, {"interview_id": interview_id})
    interview = await cur.fetchone()
    if not interview:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )

    get_conversation_query = """
    SELECT
        ic.id AS conversation_id,
        ic.transcript_data,
        ic.type as source,
        ic.created_at,
        COALESCE(
            json_agg(
                json_build_object(
                    'conversation', ich.conversation,
                    'created_at', ich.created_at
                )
            ) FILTER (WHERE ich.id IS NOT NULL),
            '[]'
        ) AS edited_field
    FROM
        interview_conversation ic
    LEFT JOIN
        interview_conversation_history ich
        ON ich.interview_conversation_id = ic.id
    WHERE
        ic.interview_id = %(interview_id)s
    GROUP BY
        ic.id
    ORDER BY
        ic.created_at ASC
    """

    await cur.execute(get_conversation_query, {"interview_id": interview_id})
    conversations = await cur.fetchall()

    return {"conversations": conversations}


async def edit_conversation(conversation_id: int, conversation: str, db):
    conn, cur = db
    check_conversation_exist_query = """
    SELECT
        ic.id
    FROM
        interview_conversation ic
    JOIN
        interview i ON i.id = ic.interview_id
    JOIN
        interview_status ins ON ins.interview_id = i.id and end_time = '2100-01-01 00:00:00+00' AND status not in ('COMPLETED','SCHEDULED')
    WHERE
        ic.id = %(conversation_id)s
    """
    await cur.execute(
        check_conversation_exist_query, {"conversation_id": conversation_id}
    )
    conversation_data = await cur.fetchone()
    if conversation_data:
        insert_into_conversation_history_query = """
        INSERT INTO
            interview_conversation_history
        (interview_conversation_id,conversation)
        VALUES
            (%(interview_conversation_id)s,%(conversation)s)
        """
        await cur.execute(
            insert_into_conversation_history_query,
            {
                "conversation": conversation,
                "interview_conversation_id": conversation_id,
            },
        )
        return {"message": "Conversation Updated"}
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Conversation Not Found Or Completed"},
        )
