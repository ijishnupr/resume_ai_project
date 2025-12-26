import asyncio
import json
import os
from datetime import datetime
from typing import Any, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv()
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

PRESCREENING_QUESTION_PROMPT = r"""
You are an experienced HR professional (8–10 years) conducting a GENERIC PRESCREENING conversation (single phase, voice-only).
Generate ONLY practical HR prescreening questions using natural 'you' language that works for ANY resume. 75% of questions MUST be standard pre-screening topics. Keep resume-specific follow-ups minimal (one-liners only).

PRESCREENING PRIORITY (75% of questions MUST cover these):
1. Current role & responsibilities (focus=prescreening)
2. Notice period / Availability (focus=availability)
3. Compensation expectations (focus=compensation)
4. Relocation willingness (focus=relocation)
5. Work authorization status (focus=authorization)
6. Work preference (remote/hybrid/onsite) (focus=work_preference)
7. Career transition motivation (focus=prescreening)
8. Employment type preference (focus=employment_type)
9. Travel flexibility (focus=travel)
10. Shift/on-call availability (focus=shift)

RESUME FOLLOW-UPS (25% maximum, one-liner only):
- Brief skill verification (focus=skills)
- Quick project clarification (focus=project)
- Tech stack confirmation (focus=tech_stack)

CORE RULES:
- Questions must work for ANY resume, not specific to one candidate
- 75% pre-screening (compensation, availability, relocation, authorization, work preferences)
- 25% or less resume-specific (keep as short one-liners) - ONLY IF DOCUMENTS PROVIDED
- If NO resume/JD: Generate 100% generic prescreening questions only
- No deep technical drilling
- Use natural "you" language throughout for conversational tone
- Professional and respectful communication

ADAPTATION RULES (apply only when contextual trigger exists in JD/resume):
- Technologies in JD → ask for RECENT practical usage & scale (tech_stack).
- Leadership terms (lead, manager, mentoring) → one scope clarification (resume/project).
- Visa / sponsorship / country → one authorization question (authorization).
- Remote/hybrid/onsite keywords → one preference alignment (work_preference).
- Travel percentage / "travel" → one travel willingness (travel).
- "on-call" / "shift" / "rotational" → one scheduling feasibility (shift).
- Equity / ESOP / bonus → one neutral factual clarification (equity).
- Contract / freelance mention → one employment type clarity (employment_type).

STRICT EXECUTION RULES:
- One clear, single-purpose question per entry (no multi-part).
- Neutral, mature, concise tone. No coaching, praise, or negotiation.
- Voice-only: no requests for code writing, diagrams, math, algorithms.
- Follow_up ONLY if it deepens factual clarity (scope, scale, quant impact); ≤ 40% of questions.
- Keep compensation phrasing neutral: "current / expected total annual compensation range".
- If data already explicit in resume/JD, refine (scope, scale) instead of repeating.

MAPPING GUIDANCE (do NOT output this section; just follow it):
- Reason for change → focus=resume (treat as career context)
- Team size / collaboration / leadership → focus=resume or project
- If lacking triggers for relocation/work_preference/etc., omit those categories.

INPUT JOB DESCRIPTION:
{job_description}

INPUT CANDIDATE RESUME:
{candidate_resume}

JOB METADATA (JSON):
{job_metadata}

OUTPUT JSON SCHEMA EXACTLY:
{
   "job_title": "<extracted role title from job description>",
   "prescreening_questions": [
      {
         "focus": "<resume|jd|tech_stack|project|compensation|availability|relocation|authorization|work_preference|travel|shift|employment_type|equity>",
         "question": "<concise professional prescreening question>",
         "follow_up": "<optional short follow-up probing depth, or empty string>"
      }
   ]
}

VALIDATION REQUIREMENTS:
1. Total questions: 12–14 (NEVER exceed 14).
2. PRE-SCREENING FOCUS (75%): 9-11 questions covering: compensation, availability, relocation, authorization, work_preference, employment_type, travel, shift, career motivation.
3. RESUME FOLLOW-UPS (25%): 3-4 maximum, one-liner questions only about skills/projects.
4. MANDATORY: 1 compensation, 1 availability, 1 relocation, 1 authorization, 1 work_preference.
5. Follow_up must be ≤ 10 words (short one-liners only).
6. No candidate names - use "the candidate" throughout.
7. Gender-neutral pronouns only (they/them/their, not he/she/his/her).
8. Questions must be generic enough to work for ANY resume.

EXAMPLES (PRE-SCREENING 75%):
prescreening: "What is your current role and key responsibilities?"
compensation: "What is your expected annual compensation range?"
availability: "What is your notice period?"
relocation: "Are you open to relocating if required?"
authorization: "Do you have valid work authorization?"
work_preference: "Do you prefer remote, hybrid, or onsite work?"
employment_type: "Are you seeking permanent or contract roles?"
travel: "Are you comfortable with travel requirements?"
shift: "Can you participate in shift work if needed?"

EXAMPLES (RESUME FOLLOW-UPS 25%, one-liners only):
skills: "What are your primary technical skills?" (follow_up: "How many years of experience?")
project: "Can you describe one recent project?" (follow_up: "What was the outcome?")
tech_stack: "Which technologies have you used recently?" (follow_up: "In what capacity?")

AVOID:
Multi-part compound questions
Hypothetical design / algorithm prompts
Vague prompts ("Tell me about yourself", "Explain strengths")
Negotiation language ("Would you accept", "Can we adjust")

Return ONLY the JSON. No commentary, no markdown.
"""


def fallback_questions() -> dict:
    """Return generic pre-screening questions (75% focus) that work for any resume."""
    return {
        "job_title": "the role",
        "prescreening_questions": [
            {
                "focus": "prescreening",
                "question": "What is your current role and key responsibilities?",
                "follow_up": "",
            },
        ],
    }


class PrescreeningQuestion(BaseModel):
    """Single prescreening question for LLM generation."""

    focus: str = Field(
        ...,
        description="Category: resume|compensation|availability|relocation|authorization|work_preference|travel|shift|employment_type",
    )
    question: str = Field(..., description="Question text")
    follow_up: str = Field(default="", description="Optional follow-up")


class PrescreeningQuestionSet(BaseModel):
    """Complete prescreening question set from LLM."""

    job_title: str = Field(default="the role")
    prescreening_questions: list[PrescreeningQuestion] = Field(default_factory=list)


class PrescreeningResponse(BaseModel):
    """Response from prescreening question generation."""

    success: bool
    data: PrescreeningQuestionSet
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class JobRequisitionContext(BaseModel):
    """Job requisition data for prescreening generation.

    Maps exactly to job_requisition table fields.
    """

    id: Optional[str] = None
    job_description_id: Optional[str] = None
    job_owner_id: Optional[int] = None
    open_positions: Optional[int] = None
    salary_type: Optional[str] = None  # enum_job_requisition_salary_type
    salary_value: Optional[str] = None
    currency: Optional[str] = None
    locations: Optional[list[dict[str, Any]]] = None  # JSONB
    work_mode: Optional[
        str
    ] = None  # enum_job_requisition_work_mode (remote|hybrid|onsite)
    start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    hours_per_week: Optional[int] = None
    duration: Optional[dict[str, Any]] = None  # JSONB
    status: Optional[str] = None  # enum_job_requisition_status
    job_type: Optional[str] = None  # enum_job_requisition_job_type
    metadata: Optional[dict[str, Any]] = None
    created_by: Optional[int] = None


class JobDescriptionContext(BaseModel):
    """Job description data for prescreening generation.

    Maps exactly to job_description table fields.
    """

    id: Optional[str] = None
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    min_yoe: Optional[float] = None
    max_yoe: Optional[float] = None
    education: Optional[str] = None
    must_have_skills: Optional[list[str]] = None
    nice_to_have_skills: Optional[list[str]] = None
    responsibilities: Optional[list[str]] = None
    jd_insights: Optional[Any] = None  # DB can store text or array
    jd_clarity: Optional[Any] = None  # DB can store text or array
    experience_band_tag: Optional[str] = None
    domain_tag: Optional[str] = None


class QuestionPrescreeningRecord(BaseModel):
    """Maps exactly to question_prescreening table.

    Used for persisting generated questions to DB.
    """

    id: Optional[str] = None
    job_requisition_id: str
    job_description_id: str
    question_text: str
    preferred_answer: Optional[str] = None
    is_mandatory: bool = True
    created_by: str = "AI"  # AI | recruiter
    metadata: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class QuestionPrescreenResponseRecord(BaseModel):
    """Maps exactly to question_prescreen_response table.

    Used for storing candidate responses during voicebot execution.
    """

    id: Optional[str] = None
    question_id: str
    resume_detail_id: str
    interview_session_id: str
    candidate_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class InterviewQuestionSessionRecord(BaseModel):
    """Maps exactly to interview_question_session table.

    Used for tracking interview sessions.
    """

    id: Optional[str] = None
    resume_detail_id: Optional[str] = None
    job_description_id: Optional[str] = None
    interview_mode: str = "prescreen"  # prescreen | technical
    status: str = "pending"  # pending | in_progress | completed | terminated
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_minutes: Optional[int] = None
    termination_reason: Optional[str] = None  # abrupt | graceful
    transcript: Optional[dict[str, Any]] = None
    ai_detected_response: Optional[dict[str, Any]] = None
    annotated_response: Optional[dict[str, Any]] = None
    tab_switch_count: Optional[int] = None
    time_spent_per_question: Optional[dict[str, Any]] = None
    audio_url: Optional[str] = None
    transcription_url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


# Initialize the client globally (standard for functional patterns)
# Or pass it as an argument if you prefer dependency injection
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def to_prescreening_schema(data: dict) -> PrescreeningQuestionSet:
    """Helper: Converts raw dictionary data to PrescreeningQuestionSet schema."""
    questions = []
    for q in data.get("prescreening_questions", []):
        questions.append(
            PrescreeningQuestion(
                focus=q.get("focus", "prescreening"),
                question=q.get("question", ""),
                follow_up=q.get("follow_up", ""),
            )
        )

    return PrescreeningQuestionSet(
        job_title=data.get("job_title", "the role"), prescreening_questions=questions
    )


async def generate_prescreening_questions(
    jd_text: str = "",
    resume_text: str = "",
    job_metadata: Optional[dict] = None,
    jr_context: Optional[JobRequisitionContext] = None,
    jd_context: Optional[JobDescriptionContext] = None,
) -> PrescreeningQuestionSet:
    """
    Function-based generator for prescreening questions.
    """
    # 1. Build metadata from contexts
    metadata = job_metadata or {}

    if jr_context:
        metadata.update(
            {
                "work_mode": jr_context.work_mode,
                "locations": jr_context.locations,
                "salary_type": jr_context.salary_type,
                "salary_value": jr_context.salary_value,
                "job_type": jr_context.job_type,
                "start_date": jr_context.start_date,
                "duration": jr_context.duration,
            }
        )

    if jd_context:
        if jd_context.job_description:
            jd_text = jd_context.job_description
        metadata.update(
            {
                "job_title": jd_context.job_title,
                "min_yoe": jd_context.min_yoe,
                "max_yoe": jd_context.max_yoe,
                "must_have_skills": jd_context.must_have_skills,
                "nice_to_have_skills": jd_context.nice_to_have_skills,
            }
        )

    # Filter None values and serialize
    metadata = {k: v for k, v in metadata.items() if v is not None}
    metadata_str = json.dumps(metadata, ensure_ascii=False, sort_keys=True, default=str)

    # 2. Prepare Prompt
    prompt = (
        PRESCREENING_QUESTION_PROMPT.replace("{job_description}", jd_text[:2000])
        .replace("{candidate_resume}", resume_text[:2000])
        .replace("{job_metadata}", metadata_str[:1000])
    )
    prompt += "\n\nIMPORTANT: Include extracted job_title field. Respect ordering and metadata rules strictly."

    try:
        # 3. Call OpenAI (Async)
        resp = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer. Always respond with valid JSON that includes job_title field.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"},  # Force JSON mode if using gpt-4o
        )

        txt = resp.choices[0].message.content.strip()

        # 4. Extract and Clean JSON
        if "```json" in txt:
            txt = txt.split("```json")[1].split("```")[0].strip()
        elif "```" in txt:
            txt = txt.split("```")[1].split("```")[0].strip()
        print(txt)
        if not txt:
            return to_prescreening_schema(fallback_questions())

        questions = json.loads(txt)

        # 5. Normalize legacy formats (Technical/Project/Behavioral)
        if "prescreening_questions" not in questions:
            merged = []
            for arr_name in [
                "technical_questions",
                "project_questions",
                "behavioral_questions",
            ]:
                for q in questions.get(arr_name, []):
                    merged.append(
                        {
                            "focus": "resume",
                            "question": q.get("question")
                            or q.get("follow_up")
                            or "Describe a relevant experience.",
                            "follow_up": q.get("follow_up", "") or q.get("context", ""),
                        }
                    )
            questions = {
                "job_title": questions.get("job_title", "Candidate"),
                "prescreening_questions": merged[:10],
            }
            print(questions)

        return to_prescreening_schema(questions)

    except Exception as e:
        # log error here
        print(f"Error: {e}")
        return to_prescreening_schema(fallback_questions())


async def main():
    print("Generating questions... please wait.")

    # We call the function here
    result = await generate_prescreening_questions(
        jd_text="Senior Python Developer with 5 years experience in FastAPI.",
        resume_text="John Doe, Backend Engineer, 6 years experience with Django and Postgres.",
    )

    # Print the results to the console
    print(f"\nJOB TITLE: {result.job_title}")
    print("-" * 30)
    for i, q in enumerate(result.prescreening_questions, 1):
        print(f"{i}. [{q.focus}] {q.question}")
        if q.follow_up:
            print(f"   Follow-up: {q.follow_up}")


# This is the standard way to run an async script in Python
if __name__ == "__main__":
    asyncio.run(main())
