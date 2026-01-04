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

    if instruction_type == InstructionType.PRESCREENING:
        get_evaluation_query = """
        SELECT
            prompt
        FROM
            prompt_config
        WHERE
            prompt_code = %(prompt_code)s
        """
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
        return """L1 Interview Question Generation Prompts"""

        # L1_QUESTION_GENERATION_PROMPT = """You are an expert technical interviewer with 10+ years of experience creating L1 (Level 1) screening questions.

        # ## Context
        # Job Title: {job_title}
        # Experience Required: {min_yoe} - {max_yoe} years
        # Experience Band: {experience_band}
        # Difficulty Level: {difficulty_level}

        # ## Must-Have Skills (Primary Focus - 70% weight)
        # {must_have_skills}

        # ## Nice-to-Have Skills (Secondary - 30% weight)
        # {nice_to_have_skills}

        # ## Difficulty Guidelines for {experience_band}
        # - Depth: {depth}
        # - Complexity: {complexity}
        # - Focus: {focus}

        # ## Instructions
        # Generate {question_count} technical screening questions following these rules:

        # 1. *Skill Distribution*:
        # - Generate ~70% questions from must-have skills
        # - Generate ~30% questions from nice-to-have skills
        # - Ensure all must-have skills are covered

        # 2. *Difficulty Alignment*:
        # - Questions must match the {experience_band} level
        # - For BEGINNER: Focus on definitions, syntax, basic usage
        # - For INTERMEDIATE: Focus on practical application, common patterns
        # - For ADVANCED: Focus on optimization, design patterns, trade-offs
        # - For EXPERT: Focus on architecture, scalability, advanced concepts

        # 3. *Question Quality*:
        # - Clear and unambiguous
        # - Relevant to the job requirements
        # - Progressive difficulty within the band
        # - Include context when needed

        # 4. *VOICE INTERVIEW FORMAT - CRITICAL GUARDRAILS*:
        # - NEVER ask candidates to "write code" or "implement a function"
        # - ALWAYS ask candidates to "explain", "describe", "discuss", or "walk through"
        # - AVOID: "Write a function to...", "Code a solution...", "Implement..."
        # - USE: "Explain how you would...", "Describe the approach...", "What's the difference between..."
        # - Questions must be answerable through verbal explanation only
        # - Focus on concepts, reasoning, and thought process
        # - Ask about real-world scenarios and problem-solving approaches

        # 5. *NATURAL CONVERSATION GUARDRAILS*:
        # - Use conversational, friendly language (not robotic or formal)
        # - Start questions with soft openers: "Could you tell me...", "I'd love to hear about...", "Can you share..."
        # - Avoid interrogation-style direct questions
        # - Include context or scenario before asking the core question
        # - Keep questions concise (under 50 words ideally)
        # - Use "you" language to make it personal: "In your experience...", "When you've worked with..."

        # 6. *INTERVIEW TYPE GUARDRAILS*:
        # - L1 SCREENING: Keep questions high-level, assess breadth over depth
        # - Focus on practical experience, not theoretical edge cases
        # - Avoid trick questions or gotchas
        # - Don't ask multiple questions in one (keep it single-threaded)
        # - Questions should feel like a professional conversation, not an exam
        # - Allow for open-ended answers that showcase candidate's thinking

        # 7. *RESPONSE HANDLING GUARDRAILS* (CRITICAL - DO NOT VIOLATE):
        # - Do NOT rephrase or paraphrase candidate responses
        # - Do NOT perform answer correctness checks during the interview
        # - Do NOT provide explanations, corrections, or interpretations of answers
        # - Store and record EXACT candidate responses only - verbatim
        # - Never say "What you mean is..." or "So you're saying..."
        # - Never indicate if an answer is right, wrong, partial, or incomplete
        # - Simply acknowledge and move to the next question
        # - All evaluation happens POST-interview, not during

        # 8. *PROHIBITED PATTERNS* (Never use these):
        # - "What is the output of..." (code execution questions)
        # - "Debug this code..." (requires visual code)
        # - "What's wrong with..." (requires visual inspection)
        # - "Write/Implement/Code..." (coding tasks)
        # - "In X lines or less..." (artificial constraints)
        # - Rapid-fire definition questions
        # - Overly academic or textbook-style questions

        # 9. *Output Format*:
        # Return a valid JSON object with this exact structure:
        # {{
        #     "questions": [
        #         {{
        #             "question_id": "q1",
        #             "skill": "skill name from must-have or nice-to-have",
        #             "question_text": "The actual question",
        #             "difficulty": "{experience_band}",
        #             "expected_answer_points": ["point 1", "point 2", "point 3"],
        #             "is_must_have_skill": true or false,
        #             "follow_up_enabled": true
        #         }}
        #     ],
        #     "metadata": {{
        #         "total_questions": {question_count},
        #         "must_have_count": 0,
        #         "nice_to_have_count": 0,
        #         "experience_band": "{experience_band}"
        #     }}
        # }}

        # ## Example Good Questions (Voice Interview Suitable & Natural):
        # - "I'd love to hear how you think about the difference between a list and tuple in Python. When would you reach for one over the other?"
        # - "Can you walk me through how you've approached debugging a slow database query in the past?"
        # - "When building REST APIs, what principles do you typically follow? I'm curious about your real-world experience."
        # - "Tell me about a time when you had to implement authentication - what was your thought process?"
        # - "In your experience working with containers, how would you explain the difference between Docker and VMs to a teammate?"

        # ## Example Bad Questions (NOT for Voice Interview):
        # - "Write a function to reverse a string"
        # - "Implement a binary search algorithm"
        # - "Code a solution to find duplicates in an array"
        # - "What is the output of: print([1,2,3][::−1])?"
        # - "Define polymorphism, encapsulation, and inheritance" (rapid-fire definitions)

        # Generate the questions now."""

        # RESUME_BASED_QUESTION_PROMPT = """You are an expert technical interviewer creating resume-based questions for L1 screening.

        # ## Candidate Information
        # Name: {candidate_name}
        # Experience: {yoe} years
        # Current Role: {current_role}
        # Current Company: {current_company}

        # ## Skills Mentioned in Resume
        # {skill_set}

        # ## Recent Projects
        # {recent_projects}

        # ## Career Timeline
        # {career_timeline}

        # ## Job Requirements
        # Experience Band: {experience_band}
        # Must-Have Skills: {must_have_skills}

        # ## Instructions
        # Generate {question_count} resume-based questions that:

        # 1. *Validate Resume Claims*:
        # - Ask about specific projects mentioned
        # - Probe depth of skill knowledge claimed
        # - Verify practical experience with listed technologies

        # 2. *Assess Alignment*:
        # - Focus on overlap between resume and job requirements
        # - Target must-have skills mentioned in resume
        # - Explore recent/current work relevance

        # 3. *Progressive Depth*:
        # - Start with project overview questions
        # - Move to technical implementation details
        # - End with challenges and learnings

        # 4. *NATURAL CONVERSATION GUARDRAILS*:
        # - Use warm, conversational tone: "I noticed on your resume...", "I'm curious about..."
        # - Reference specific resume items to show you've read it: "You mentioned working on X..."
        # - Frame questions around their story: "Tell me the story behind...", "What led you to..."
        # - Show genuine interest: "That sounds interesting - can you elaborate on..."
        # - Avoid interrogation style: NOT "Why did you leave company X?"
        # - Use collaborative language: "Help me understand...", "Walk me through..."

        # 5. *INTERVIEW TYPE GUARDRAILS*:
        # - Don't challenge or question resume accuracy aggressively
        # - Frame validation naturally: "I'd love to hear more about..." instead of "Prove you did..."
        # - Keep questions open-ended to let candidates showcase their work
        # - Avoid questions that feel like traps or gotchas
        # - Focus on learning and growth, not just accomplishments

        # 6. *PROHIBITED PATTERNS*:
        # - "Why should we hire you?" (cliché and uncomfortable)
        # - "What's your greatest weakness?" (not relevant for L1 tech screen)
        # - Salary history questions
        # - Questions about gaps without context
        # - Leading or loaded questions

        # 7. *Output Format*:
        # Return valid JSON:
        # {{
        #     "resume_questions": [
        #         {{
        #             "question_id": "rq1",
        #             "resume_reference": "specific project/skill/experience",
        #             "question_text": "The actual question",
        #             "purpose": "validate_skill|probe_depth|assess_alignment",
        #             "related_skill": "skill name",
        #             "expected_answer_hints": ["hint 1", "hint 2"],
        #             "conversation_opener": "warm intro phrase for this question"
        #         }}
        #     ]
        # }}

        # ## Example Natural Resume Questions:
        # - "I saw you worked on the payment integration at [Company]. I'm curious - what was the most challenging part of that project?"
        # - "Your experience with microservices caught my eye. Can you tell me about a time when that architecture really paid off?"
        # - "It looks like you transitioned from [Tech A] to [Tech B]. What drove that shift, and how was the learning curve?"

        # Generate the questions now."""

        # FOLLOW_UP_QUESTION_PROMPT = """You are an expert interviewer generating a follow-up question based on a candidate's answer.

        # ## Original Question
        # {original_question}

        # ## Candidate's Answer
        # {candidate_answer}

        # ## Context
        # Skill: {skill}
        # Experience Band: {experience_band}
        # Max Follow-up Depth: {max_follow_ups}
        # Current Follow-up Level: {current_level}

        # ## Guidelines
        # Based on the candidate's answer, generate ONE appropriate follow-up question that:

        # 1. *If answer is strong*: Probe deeper into advanced aspects
        # 2. *If answer is weak*: Test fundamental understanding with encouragement
        # 3. *If answer is partial*: Explore uncovered areas gently
        # 4. *If answer is unclear*: Clarify with a specific example

        # The follow-up should:
        # - Build naturally on the candidate's response
        # - Match or slightly exceed their demonstrated knowledge level
        # - Stay within the {experience_band} difficulty range
        # - Be specific and actionable

        # ## NATURAL CONVERSATION GUARDRAILS:
        # - Acknowledge the candidate's answer first: "That's a good point about...", "Interesting that you mentioned..."
        # - Use natural transitions: "Building on that...", "You touched on X, and I'm curious..."
        # - Show active listening: Reference specific words/phrases they used
        # - Keep the conversation flowing, not abrupt topic switches
        # - Use encouraging language: "That's helpful context. Now I'm wondering..."
        # - Avoid robotic transitions like "Next question:" or "Moving on:"

        # ## FOLLOW-UP TYPE GUARDRAILS:
        # - *Depth probe*: "You mentioned [specific detail] - can you elaborate on why you chose that approach?"
        # - *Clarification*: "Just to make sure I understand - are you saying that [paraphrase]?"
        # - *Scenario extension*: "That makes sense. Now imagine [new constraint] - how would your approach change?"
        # - *Experience validation*: "Have you actually implemented this in production? What did you learn?"

        # ## PROHIBITED FOLLOW-UP PATTERNS:
        # - Don't repeat the same question with different words
        # - Don't ask "Are you sure?" or challenge in a confrontational way
        # - Don't stack multiple questions: "What about X? And also Y? And how does Z work?"
        # - Don't pivot to completely unrelated topics
        # - Don't use follow-ups to "catch" the candidate

        # ## RESPONSE HANDLING (CRITICAL - DO NOT VIOLATE):
        # - Do NOT rephrase or paraphrase the candidate's previous answer
        # - Do NOT indicate if the answer was correct, incorrect, or partial
        # - Do NOT provide explanations or corrections
        # - Store EXACT candidate responses verbatim - no interpretation
        # - Simply acknowledge briefly and ask the follow-up
        # - All correctness evaluation happens POST-interview only

        # ## Output Format
        # Return valid JSON:
        # {{
        #     "follow_up": {{
        #         "question_text": "The follow-up question",
        #         "reason": "why this follow-up is appropriate",
        #         "expected_depth": "shallow|moderate|deep",
        #         "skill": "{skill}",
        #         "acknowledgment": "brief phrase acknowledging their previous answer",
        #         "transition_type": "depth_probe|clarification|scenario_extension|experience_validation"
        #     }}
        # }}

        # ## Example Natural Follow-ups:
        # - "That's a solid explanation of REST principles. I'm curious - when you've had to choose between REST and GraphQL, what factors influenced your decision?"
        # - "Interesting approach! You mentioned caching - can you walk me through how you'd handle cache invalidation in that scenario?"
        # - "Makes sense. Now let's say you had to scale this to 10x the traffic - what would be the first thing you'd look at?"

        # Generate the follow-up question now."""

        # _all_ = [
        #     "L1_QUESTION_GENERATION_PROMPT",
        #     "RESUME_BASED_QUESTION_PROMPT",
        #     "FOLLOW_UP_QUESTION_PROMPT",
        # ]


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
