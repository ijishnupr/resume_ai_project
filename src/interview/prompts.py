from enum import Enum


class InstructionType(str, Enum):
    PRESCREENING = "PRESCREENING"
    L1 = "L1"


async def get_base_instructions(
    db,
    instruction_type: InstructionType,
    job_title: str,
    candidate_resume: str,
    job_description: str,
    generated_questions_section: str,
    custom_questions_section: str,
):
    conn, cur = db
    get_evaluation_query = """
        SELECT
            prompt
        FROM
            prompt_config
        WHERE
            prompt_code = %(prompt_code)s
        """
    if instruction_type == InstructionType.PRESCREENING:
        await cur.execute(
            get_evaluation_query, {"prompt_code": "pre_screening_question_generation"}
        )
        row = await cur.fetchone()

        if not row or not row.get("prompt"):
            raise ValueError("Prompt not found for pre_screening_question_generation")

        prompt_template: str = row["prompt"]

        final_prompt = prompt_template.format(
            job_title=job_title,
            candidate_resume=candidate_resume,
            job_description=job_description,
            generated_questions_section=generated_questions_section,
            custom_questions_section=custom_questions_section,
        )

        return final_prompt
    else:
        await cur.execute(
            get_evaluation_query, {"prompt_code": "l1_question_generation"}
        )


async def get_evaluation_prompt(
    db,
    instruction_type: InstructionType,
    conversation_text: str,
    job_description: str = "",
    resume: str = "",
    job_metadata: dict | None = None,
):
    conn, cur = db

    get_evaluation_query = """
    SELECT
        prompt
    FROM
        prompt_config
    WHERE
        prompt_code = %(prompt_code)s
    """

    if instruction_type == InstructionType.PRESCREENING:
        prompt_code = "pre_screening_evaluation"
    elif instruction_type == InstructionType.L1:
        prompt_code = "l1_evaluation"
    else:
        raise ValueError("Unsupported instruction type")

    await cur.execute(get_evaluation_query, {"prompt_code": prompt_code})
    row = await cur.fetchone()

    if not row or not row.get("prompt"):
        raise ValueError(f"Prompt not found for {prompt_code}")

    prompt_template: str = row["prompt"]

    final_prompt = prompt_template.format(
        conversation_text=conversation_text,
        job_description=job_description,
        resume=resume,
        job_metadata=job_metadata or "None",
    )

    return final_prompt
