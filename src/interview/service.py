import datetime
from psycopg.types.json import Jsonb
import os

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

from src.interview.model import (
    ConversationRequest,
    PatchInterviewViolation,
)
from src.interview.prompts import InstructionType, get_base_instructions
from src.shared.dependency import UserPayload

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


async def open_ai(prompt):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/realtime/sessions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-realtime-preview-2024-12-17",
                "voice": "alloy",
                "instructions": prompt,
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="Failed to create session"
            )

        return response.json()


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
    ciqs.id,
    ciqs.created_at,
    ciqs.status,
    UPPER(ciqs.interview_mode) AS interview_type,
    'Ylogx' AS company_name,

    jd.job_title,
    jd.job_description,


    -- Resume Data (Bundled as JSON Dict)
    jsonb_build_object(
        'name', rd.name,
        'raw_text', rd.cf_text,
        'skills', rd.skill_set,
        'experience', rd.work_experience,
        'details', rd.details
    ) AS candidate_resume,

    -- Prescreening Questions (Aggregated into a List of JSON Objects)
    (
        SELECT jsonb_agg(
            jsonb_build_object(
                'question_text', sub_cqp.question_text,
                'preferred_answer', sub_cqp.preferred_answer,
                'is_mandatory', sub_cqp.is_mandatory,
                'created_by', sub_cqp.created_by
            )
        )
        FROM candidate_question_prescreening sub_cqp
        WHERE sub_cqp.job_requisition_id = ciqs.job_requisition_id
    ) AS prescreen_questions

    FROM
        candidate_interview_question_session ciqs
    LEFT JOIN
        job_description jd ON ciqs.job_description_id = jd.id
    LEFT JOIN
        resume_detail rd ON ciqs.resume_detail_id = rd.id
    WHERE
        ciqs.id = %(interview_id)s;
    """

    await cur.execute(get_interview_query, {"interview_id": interview_id})
    interview_data = await cur.fetchone()

    return interview_data


async def get_ephemeral_token(interview: dict):
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
    response = await open_ai(instructions)
    return response, instructions


async def start_interview(interview_id: str, user: UserPayload, db):
    conn, cur = db
    interview = await get_interview_details(interview_id, db)
    if interview and interview["status"] != "pending":
        return {"message": "Token Already generated"}
    token, instructions = await get_ephemeral_token(interview)
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

    return token["client_secret"], instructions


async def insert_conversation(
    interview_id: str,
    request: ConversationRequest,
    db,
):
    conn, cur = db

    data = {
        "ai": request.ai,
        "user": request.user,
        "time_stamp": str(datetime.datetime.now()),
    }

    update_query = """
    UPDATE candidate_interview_question_session
    SET
        transcript = COALESCE(transcript, '[]'::jsonb) || %(new_item)s,
        updated_at = CURRENT_TIMESTAMP
    WHERE
        id = %(interview_id)s
    RETURNING id;
    """

    await cur.execute(
        update_query,
        {
            "interview_id": interview_id,
            "new_item": Jsonb([data]),
        },
    )

    updated = await cur.fetchone()
    if not updated:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )

    return {"message": "Conversation Updated"}


async def update_interview_status(interview_id: str, interview_status: str, db):
    conn, cur = db
    check_interview_query = """
    SELECT
        id,
        transcript
    FROM
        candidate_interview_question_session
    WHERE
        id = %(interview_id)s AND termination_reason not in ('abrupt','graceful')
    """
    await cur.execute(check_interview_query, {"interview_id": interview_id})
    interview = await cur.fetchone()
    if not interview:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )
    # conversation = interview["transcript"]

    # prompt = f"This interview violated the interview this is the conversation he had with the interviewer{conversation}"
    # ai_detected_response = await open_ai(prompt)

    update_interview_status_query = """
    UPDATE
        candidate_interview_question_session
    SET
        termination_reason = %(interview_status)s,
        ai_detected_response = %(ai_detected_response)s

    WHERE
        id = %(interview_id)s

    """
    await cur.execute(
        update_interview_status_query,
        {
            "interview_status": interview_status,
            "interview_id": interview_id,
            "ai_detected_response": Jsonb(interview["transcript"]),
        },
    )

    return {"message": "Interview Status Updated"}


async def get_conversation(interview_id: str, db):
    conn, cur = db
    check_interview_available_query = """
    SELECT

        i.ai_detected_response,
        i.annotated_response

    FROM
        candidate_interview_question_session i
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

    await cur.execute(check_interview_available_query, {"interview_id": interview_id})
    conversations = await cur.fetchone()

    return conversations


async def edit_conversation(interview_id: str, index: int, conversation: str, db):
    conn, cur = db
    get_interview_query = """
    SELECT
        transcript
    FROM
        candidate_interview_question_session
    WHERE
        id = %(interview_id)s
    """
    await cur.execute(get_interview_query, {"interview_id": interview_id})
    interview = await cur.fetchone()
    if not interview:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )

    transcript = interview["transcript"]
    if index < 0 or index >= len(transcript):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "Invalid conversation index"},
        )

    updated_transcript = transcript.copy()
    updated_transcript[index] = {
        **updated_transcript[index],
        "user": conversation,
        "edited_at": str(datetime.datetime.now()),
    }
    update_interview_query = """
    UPDATE
        candidate_interview_question_session
    SET
        annotated_response = %(updated_transcript)s
    WHERE
        id = %(interview_id)s

    """
    await cur.execute(
        update_interview_query,
        {"updated_transcript": Jsonb(updated_transcript), "interview_id": interview_id},
    )
    return {"message": "Conversation Updated"}


async def update_interview_violation(
    interview_id: str, request: PatchInterviewViolation, db
):
    conn, cur = db
    update_termination_reason_query = """
    INSERT INTO
        interview_violation
    (interview_session_id,violation_type,description)
    VALUES(
        %(interview_id)s,%(violation_type)s,%(description)s
    )

    """
    await cur.execute(
        update_termination_reason_query,
        {
            "violation_type": request.violation,
            "interview_id": interview_id,
            "description": request.description,
        },
    )
    return {"message": "Termination Details Updated"}
