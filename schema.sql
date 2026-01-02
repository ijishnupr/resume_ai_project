CREATE TABLE candidate_user (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(225),
    password TEXT ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    email VARCHAR(255) UNIQUE,
    is_reset_password BOOLEAN DEFAULT FALSE
);




CREATE TABLE interview_violation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_session_id UUID,
    violation_type VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE candidate_user_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_user_id UUID NOT NULL REFERENCES candidate_user(id) ON DELETE CASCADE,
    refresh_token TEXT NOT NULL,
    ip_address VARCHAR(50),
    user_agent TEXT,
    metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);





-- prod db schema

-- Enable extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


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
    jod_description_id UUID,
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

----------------------------------------------------------
-- FOREIGN KEY CONSTRAINTS
----------------------------------------------------------

-- resume_detail > candidate_user (Linked by ID implies 1:1 or Resume belongs to Candidate)
-- Note: resume_detail.id is used as FK here based on 'Ref: resume_detail.id > candidate_user.id'
ALTER TABLE resume_detail
ADD CONSTRAINT fk_resume_candidate_user
FOREIGN KEY (id) REFERENCES candidate_user(id);

-- job_requisition > job_description
-- (Note: Not explicitly defined in 'Ref' section but implied by column name. Added for safety)
ALTER TABLE job_requisition
ADD CONSTRAINT fk_job_req_description
FOREIGN KEY (job_description_id) REFERENCES job_description(id);

-- candidate_question_prescreen_response > candidate_question_prescreening
ALTER TABLE candidate_question_prescreen_response
ADD CONSTRAINT fk_prescreen_resp_question
FOREIGN KEY (question_id) REFERENCES candidate_question_prescreening(id);

-- candidate_question_prescreen_response > resume_detail
ALTER TABLE candidate_question_prescreen_response
ADD CONSTRAINT fk_prescreen_resp_resume
FOREIGN KEY (resume_detail_id) REFERENCES resume_detail(id);

-- candidate_question_prescreen_response > candidate_interview_question_session
ALTER TABLE candidate_question_prescreen_response
ADD CONSTRAINT fk_prescreen_resp_session
FOREIGN KEY (interview_session_id) REFERENCES candidate_interview_question_session(id);

-- candidate_interview_question_session > resume_detail
ALTER TABLE candidate_interview_question_session
ADD CONSTRAINT fk_session_resume
FOREIGN KEY (resume_detail_id) REFERENCES resume_detail(id);

-- candidate_interview_question_session > job_description
ALTER TABLE candidate_interview_question_session
ADD CONSTRAINT fk_session_job_description
FOREIGN KEY (job_description_id) REFERENCES job_description(id);

-- candidate_interview_question_session > job_requisition (from Ref list)
ALTER TABLE candidate_interview_question_session
ADD CONSTRAINT fk_session_job_req
FOREIGN KEY (job_requisition_id) REFERENCES job_requisition(id);

-- candidate_ai_interview_evaluation > candidate_interview_question_session
ALTER TABLE candidate_ai_interview_evaluation
ADD CONSTRAINT fk_evaluation_session
FOREIGN KEY (interview_session_id) REFERENCES candidate_interview_question_session(id);

-- candidate_ai_interview_evaluation > candidate_user
ALTER TABLE candidate_ai_interview_evaluation
ADD CONSTRAINT fk_evaluation_candidate
FOREIGN KEY (candidate_id) REFERENCES candidate_user(id);

-- candidate_question_prescreening > job_description
-- Note: Column name is jod_description_id (typo preserved)
ALTER TABLE candidate_question_prescreening
ADD CONSTRAINT fk_prescreening_job_description
FOREIGN KEY (jod_description_id) REFERENCES job_description(id);

-- candidate_question_prescreening > job_requisition
ALTER TABLE candidate_question_prescreening
ADD CONSTRAINT fk_prescreening_job_req
FOREIGN KEY (job_requisition_id) REFERENCES job_requisition(id);

-- candidate_technical_L1_question > job_requisition
ALTER TABLE candidate_technical_L1_question
ADD CONSTRAINT fk_tech_l1_job_req
FOREIGN KEY (job_requisition_id) REFERENCES job_requisition(id);

ALTER TABLE interview_violation
ADD CONSTRAINT inv_vol_inv_question_sess
FOREIGN KEY (interview_session_id) REFERENCES candidate_interview_question_session(id);
