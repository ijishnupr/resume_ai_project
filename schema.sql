CREATE TABLE interview_candidate (
    id SERIAL PRIMARY KEY,
    password TEXT ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE interview_candidate
ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;

ALTER TABLE interview_candidate
ADD COLUMN IF NOT EXISTS is_reset_password BOOLEAN DEFAULT FALSE;


CREATE TABLE user_session (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES interview_candidate(id) ON DELETE CASCADE,
    refresh_token TEXT UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE interview (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES interview_candidate(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_date TIMESTAMP WITH TIME ZONE

);



ALTER TABLE interview
ADD COLUMN IF NOT EXISTS job_requisition_id INT;

ALTER TABLE interview
ADD COLUMN IF NOT EXISTS resume_id INT ;



ALTER TABLE interview
ADD CONSTRAINT uq_interview_user_resume
UNIQUE (user_id, resume_id);



CREATE TYPE interview_status_enum AS ENUM (
    'SCHEDULED',
    'ACTIVE',
    'SESSION_CLOSED',
    'COMPLETED',
    'TERMINATED'
);



CREATE TABLE interview_status (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interview(id) ON DELETE CASCADE,
    status interview_status_enum NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE DEFAULT '2100-01-01 00:00:00+00'

);

CREATE TABLE interview_session(
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interview(id) ON DELETE CASCADE,
    session_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interview_violation (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interview(id) ON DELETE CASCADE,
    violation_type VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interview_question(
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interview(id) ON DELETE CASCADE,
    transcript_data TEXT,
    question VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interview_answer(
    id SERIAL PRIMARY KEY,
    interview_id INTEGER REFERENCES interview(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES interview_question(id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE candidate_user(
    id SERIAL PRIMARY KEY,
    email VARCHAR(50) UNIQUE

);

CREATE TABLE job_requisition (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500)

);

CREATE TABLE resume_detail(
    id SERIAL PRIMARY KEY,
    candidate_user_id INTEGER REFERENCES candidate_user(id) ON DELETE CASCADE,
    resume_data VARCHAR(400),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE question(
    id SERIAL PRIMARY KEY,
    question VARCHAR(500) NOT NULL,
    is_mandatory BOOLEAN DEFAULT FALSE,
    preferred_answer VARCHAR(500),
    sequence_no int NOT NULL
);

CREATE TABLE answers(
    id SERIAL PRIMARY KEY,
    answer VARCHAR(500),
    question_id INTEGER REFERENCES question(id) ON DELETE CASCADE
);
