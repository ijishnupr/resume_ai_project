import datetime
import json
import os
import re

import httpx
import openai
from dotenv import load_dotenv
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from psycopg.types.json import Jsonb

from src.interview.model import (
    ConversationRequest,
    PatchInterviewViolation,
)
from src.interview.prompts import (
    InstructionType,
    get_base_instructions,
    get_evaluation_prompt,
)
from src.shared.dependency import UserPayload

load_dotenv()
AZURE_OPENAI_REALTIME_ENDPOINT = os.getenv("AZURE_OPENAI_REALTIME_ENDPOINT")
AZURE_OPENAI_REALTIME_API_KEY = os.getenv("AZURE_OPENAI_REALTIME_API_KEY")
AZURE_OPENAI_REALTIME_VERSION = os.getenv("AZURE_OPENAI_REALTIME_VERSION")


def _normalize_highlights(highlights: list) -> list:
    if not isinstance(highlights, list):
        return [
            "Notice Period: Not specified",
            "Expected CTC: Not specified",
            "Relocation: Not specified",
        ]

    required = ["Notice Period:", "Expected CTC:", "Relocation:"]
    normalized = []
    # map for quick lookup
    for label in required:
        found = next(
            (h for h in highlights if isinstance(h, str) and h.startswith(label)), None
        )
        normalized.append(found if found else f"{label} Not specified")
    # Optional auth/work preference
    optional = next(
        (
            h
            for h in highlights
            if isinstance(h, str)
            and (h.startswith("Authorization:") or h.startswith("Work Preference:"))
        ),
        None,
    )
    if optional:
        normalized.append(optional)
    return normalized


def _build_client(api_key: str | None = None):
    """Construct OpenAI client for GPT-4o evaluation.

    Uses AZURE_OPENAI_EVAL_* or AZURE_OPENAI_* env vars (separate from realtime creds).
    """
    # GPT-4o evaluation endpoint (separate from realtime endpoint)
    azure_endpoint = (
        (
            os.getenv("AZURE_OPENAI_EVAL_ENDPOINT")
            or os.getenv("AZURE_OPENAI_ENDPOINT")
            or ""
        )
        .rstrip("/")
        .strip("'")
    )
    azure_key = (
        os.getenv("AZURE_OPENAI_EVAL_API_KEY")
        or os.getenv("AZURE_OPENAI_API_KEY")
        or api_key
    )
    azure_version = (
        os.getenv("AZURE_OPENAI_EVAL_VERSION")
        or os.getenv("OPENAI_API_VERSION")
        or "2024-05-01-preview"
    )

    if azure_endpoint and azure_key:
        return openai.AzureOpenAI(
            api_key=azure_key,
            api_version=azure_version,
            azure_endpoint=azure_endpoint,
        )

    return openai.OpenAI(api_key=api_key)


def call_open_ai(messages):
    client = _build_client()

    resp = client.chat.completions.create(
        model="gpt-4o", messages=messages, temperature=0.3, max_tokens=2500
    )
    txt = resp.choices[0].message.content.strip()

    match = re.search(r"\{[\s\S]*\}", txt)
    if not match:
        raise ValueError(f"Invalid model output, JSON not found:\n{txt}")

    data = json.loads(match.group())

    if isinstance(data, dict) and "highlights" in data:
        data["highlights"] = _normalize_highlights(data["highlights"])

    data["evaluation_metadata"] = {
        "timestamp": datetime.datetime.now().isoformat(),
        "evaluation_type": "transcript_only",
    }

    return data


async def call_open_ai_evaluation(messages):
    client = _build_client()

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.3,
        max_tokens=2500,
    )

    txt = resp.choices[0].message.content.strip()

    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", txt)
    if not match:
        raise ValueError(f"Invalid model output, JSON not found:\n{txt}")

    parsed = json.loads(match.group())

    return parsed


async def create_ai_session(prompt: str):
    async with httpx.AsyncClient(timeout=10) as client:
        session_config = {
            "session": {
                "type": "realtime",
                "model": "gpt-realtime",
                "instructions": prompt,
                "audio": {
                    "output": {
                        "voice": "marin",
                    },
                },
            },
        }
        response = await client.post(
            AZURE_OPENAI_REALTIME_ENDPOINT,
            headers={
                "Authorization": f"Bearer {AZURE_OPENAI_REALTIME_API_KEY}",
                "Content-Type": "application/json",
            },
            json=session_config,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Realtime session failed: {response.text}",
            )

        if not response.content:
            raise RuntimeError("Azure returned empty response body")

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
    ciqs.metadata,
    UPPER(ciqs.interview_mode) AS interview_type,
    'Ylogx' AS company_name,
    ciqs.interview_mode,
    jd.job_title,
    ciqs.transcript,
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


async def get_ephemeral_token(interview: dict, db):
    job_title = interview["job_title"]
    job_description = interview["job_description"]
    candidate_resume = interview["candidate_resume"]
    # generated_questions_section = interview["generated_questions_section"]
    # custom_questions_section = interview["custom_questions_section"]
    instructions = await get_base_instructions(
        db,
        InstructionType("PRESCREENING"),
        job_title,
        candidate_resume,
        job_description,
        "None",
        "None",
    )
    response = await create_ai_session(instructions)
    return response, instructions


async def start_interview(interview_id: str, user: UserPayload, db):
    conn, cur = db
    interview = await get_interview_details(interview_id, db)
    if interview and interview["status"] != "pending":
        return {"message": "Token Already generated"}
    token, instructions = await get_ephemeral_token(interview, db)
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
    return {
        "value": token["value"],
        "expires_at": token["expires_at"],
        "instructions": token["session"]["instructions"],
    }


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
        id = %(interview_id)s AND termination_reason is NULL
    """
    await cur.execute(check_interview_query, {"interview_id": interview_id})
    interview = await cur.fetchone()
    if not interview:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Interview Not Found"},
        )
    conversation = interview["transcript"]

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert interview transcript analyst. "
                "Return ONLY valid JSON. Do not include explanations, markdown, or extra text."
            ),
        },
        {
            "role": "user",
            "content": f"""Analyze this conversation transcript where speech-to-text errors have corrupted the user's responses. The AI's responses are accurate and provide context clues.

    Conversation:
    {conversation}

    Task: Reconstruct what the user likely said by:
    1. Using the AI's question/response as context
    2. Finding phonetically similar real words/phrases
    3. Ensuring responses make sense in an interview setting

    Return a JSON array with this structure:
    [
      {{
        "ai": "<original AI text>",
        "user": "<corrected user text>",
        "time_stamp": "<original timestamp>"
      }},
      ...
    ]

    Focus on making the user responses coherent, professional, and contextually appropriate.""",
        },
    ]

    ai_detected_response = await call_open_ai_evaluation(messages)

    update_interview_status_query = """
    UPDATE
        candidate_interview_question_session
    SET
        termination_reason = %(interview_status)s,
        ai_detected_response = %(ai_detected_response)s,
        annotated_response = %(ai_detected_response)s

    WHERE
        id = %(interview_id)s

    """
    await cur.execute(
        update_interview_status_query,
        {
            "interview_status": interview_status,
            "interview_id": interview_id,
            "ai_detected_response": Jsonb(ai_detected_response),
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
        ai_detected_response
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

    transcript = interview["ai_detected_response"]
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


async def update_interview_status_to_complete(interview_id: str, user: UserPayload, db):
    conn, cur = db
    interview_data = await get_interview_details(interview_id, db)
    if interview_data["interview_mode"] == "prescreen":
        prompt = await get_evaluation_prompt(
            db,
            InstructionType("PRESCREENING"),
            interview_data["transcript"],
            interview_data["job_description"],
            interview_data["candidate_resume"],
            interview_data["metadata"],
        )
        audio_file_path = False
        # Note: Audio analysis not supported in Chat Completions API
        audio_note = (
            " (Note: Audio file provided but analysis limited to transcript)"
            if audio_file_path
            else ""
        )

        messages = [
            {
                "role": "system",
                "content": f"You are an expert technical interviewer and communication evaluator. Analyze the interview transcript for comprehensive assessment.{audio_note}",
            },
            {"role": "user", "content": prompt},
        ]
        response = call_open_ai(messages)

    else:
        prompt = await get_evaluation_prompt(
            db,
            InstructionType("PRESCREENING"),
            interview_data["transcript"],
            interview_data["job_description"],
            interview_data["candidate_resume"],
            interview_data["metadata"],
        )

        audio_file_path = False
        # Note: Audio analysis not supported in Chat Completions API
        audio_note = (
            " (Note: Audio file provided but analysis limited to transcript)"
            if audio_file_path
            else ""
        )

        messages = [
            {
                "role": "system",
                "content": f"You are an expert technical interviewer and communication evaluator. Analyze the interview transcript for comprehensive assessment.{audio_note}",
            },
            {"role": "user", "content": prompt},
        ]
        response = call_open_ai(messages)
    update_interview_pre_evaluation_query = """
        INSERT INTO
            candidate_ai_interview_evaluation
        (candidate_id,interview_session_id,overall_score,evaluation_summary,ai_feedback)
        VALUES
            ( %(user_id)s,%(interview_id)s,%(overall_score)s,%(evaluation_summary)s,%(ai_feedback)s )

        """
    await cur.execute(
        update_interview_pre_evaluation_query,
        {
            "user_id": user.user_id,
            "interview_id": interview_id,
            "overall_score": response["fit_score"],
            "evaluation_summary": response["prescreening_summary"],
            "ai_feedback": Jsonb(response["evaluation_metadata"]),
        },
    )
    update_interview_status_query = """
        UPDATE
            candidate_interview_question_session
        SET
            status = 'completed'
        WHERE
            id = %(interview_id)s

        """
    await cur.execute(update_interview_status_query, {"interview_id": interview_id})
    return {"message": "Interview Status Updated"}
