CREATE TABLE candidate_user (
    id SERIAL PRIMARY KEY,
    name VARCHAR(225),
    password TEXT ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(255) UNIQUE,
    is_reset_password BOOLEAN DEFAULT FALSE
);






CREATE TABLE interview_violation (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interview(id) ON DELETE CASCADE,
    violation_type VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);







-- prod db schema

-- Enable extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

----------------------------------------------------------
-- TABLE: candidate_user
----------------------------------------------------------
CREATE TABLE candidate_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    email TEXT UNIQUE,
    url TEXT,
    username TEXT UNIQUE,
    password TEXT,
    validity TIMESTAMP
);

----------------------------------------------------------
-- TABLE: job_requisition
----------------------------------------------------------
CREATE TABLE job_requisition (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_description_id UUID,
    job_owner_id INTEGER,
    open_positions INTEGER
);

----------------------------------------------------------
-- TABLE: job_description
----------------------------------------------------------
CREATE TABLE job_description (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_title TEXT,
    job_description TEXT,
    min_yoe FLOAT,
    max_yoe FLOAT,
    education TEXT,
    must_have_skills TEXT[],
    nice_to_have_skills TEXT[],
    responsibilities TEXT[],
    jd_insights TEXT,
    jd_clarity TEXT,
    experience_band_tag VARCHAR(255),
    domain_tag VARCHAR(255),
    process_detail_id UUID,
    document_id UUID,
    metadata JSONB,
    created_by INTEGER,
    last_updated_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    org_id INTEGER
);

----------------------------------------------------------
-- TABLE: resume_detail
----------------------------------------------------------
CREATE TABLE resume_detail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID,
    source_id UUID,
    process_detail_id UUID,
    trivia_id UUID,
    name TEXT,
    phone_number TEXT[],
    email TEXT,
    yoe DOUBLE PRECISION,
    best_fit_role TEXT,
    current_company TEXT,
    start_date TEXT,
    job_title TEXT,
    qualification TEXT,
    introduction TEXT,
    work_experience TEXT,
    skill_set TEXT,
    details JSONB,
    updated_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    academics JSONB,
    certifications JSONB,
    latest_projects JSONB,
    career_timeline JSONB,
    status_reason TEXT,
    employee_referral_code TEXT,
    miscellaneous_details JSONB,
    cf_text TEXT,
    job_owner_id INTEGER,
    normalized_skills TEXT[],
    updated_by_id INTEGER,
    duplicate_flag BOOLEAN,
    duplicate_group_id UUID,
    duplicate_resolution VARCHAR(255),
    applicant_status VARCHAR(50),
    archived_at TIMESTAMP,

    CONSTRAINT check_applicant_status CHECK (applicant_status IN ('active', 'rejected', 'hired', 'archived'))
);

----------------------------------------------------------
-- TABLE: candidate_interview_question_session
----------------------------------------------------------
CREATE TABLE candidate_interview_question_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_detail_id UUID,
    job_description_id UUID,
    job_requisition_id UUID,
    interview_mode VARCHAR(50),
    status VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_duration_minutes INTEGER,
    termination_reason TEXT,
    transcript JSONB, --json from fronted
    ai_detected_response JSONB, -- open ai respnse
    annotated_response JSONB, -- edited field
    tab_switch_count INTEGER,
    time_spent_per_question JSONB,
    audio_url TEXT,
    transcription_url TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_interview_mode CHECK (interview_mode IN ('prescreen', 'technical')),
    CONSTRAINT check_session_status CHECK (status IN ('pending', 'in_progress', 'completed', 'terminated')),
    CONSTRAINT check_termination_reason CHECK (termination_reason IN ('abrupt', 'graceful'))
);

----------------------------------------------------------
-- TABLE: candidate_ai_interview_evaluation
----------------------------------------------------------
CREATE TABLE candidate_ai_interview_evaluation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID,
    interview_session_id UUID,
    overall_score DOUBLE PRECISION,
    evaluation_summary TEXT,
    ai_feedback JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

----------------------------------------------------------
-- TABLE: candidate_question_prescreening
----------------------------------------------------------
CREATE TABLE candidate_question_prescreening (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_requisition_id UUID,
    jod_description_id UUID, -- Keeping typo as per schema requirements
    question_text TEXT,
    preferred_answer TEXT,
    is_mandatory BOOLEAN,
    created_by TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT check_created_by CHECK (created_by IN ('AI', 'recruiter'))
);

----------------------------------------------------------
-- TABLE: candidate_question_prescreen_response
----------------------------------------------------------
CREATE TABLE candidate_question_prescreen_response (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID,
    resume_detail_id UUID,
    interview_session_id UUID,
    candidate_answer TEXT,
    is_correct BOOLEAN,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

----------------------------------------------------------
-- TABLE: candidate_technical_L1_question
----------------------------------------------------------
CREATE TABLE candidate_technical_L1_question (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_requisition_id UUID,
    skills_recommended JSONB,
    skills_captured JSONB,
    indicative_questions JSONB,
    technical_questions JSONB,
    recruiter_added_questions JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

----------------------------------------------------------
-- TABLE: interview_credits
----------------------------------------------------------
CREATE TABLE interview_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID,
    interview_type TEXT,
    available_minutes INTEGER,
    completed_minutes INTEGER,
    completed_count INTEGER,
    unused_links INTEGER,
    expired_links INTEGER,
    reserved_credits INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
