-- ===========================================================================
-- EduSphere — INFERRED PostgreSQL schema
-- ===========================================================================
-- The repository contains NO migration that creates most of these tables.
-- app.py and the five *_discovery.py modules reference them, so a fresh
-- database fails at startup. This file was reconstructed from every SQL
-- statement in the code (commit 9607a80).
--
-- !! VERIFY BEFORE RUNNING ON AN EXISTING DATABASE !!
-- Compare with your live Supabase/Postgres schema first:
--
--   SELECT table_name, column_name, data_type, is_nullable, column_default
--   FROM information_schema.columns
--   WHERE table_schema = 'public'
--   ORDER BY table_name, ordinal_position;
--
-- CREATE TABLE IF NOT EXISTS will NOT add missing columns to existing tables.
-- If your live tables already exist but differ, write explicit ALTER TABLE
-- statements instead of running this file.
--
-- Epoch columns (created_at, updated_at, expires_at) are BIGINT because the
-- Python code writes int(time.time()).
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- Core: used by app.py
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id            BIGSERIAL PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    admin_id   BIGINT NOT NULL REFERENCES admins(id) ON DELETE CASCADE,
    expires_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expires_at_idx ON sessions (expires_at);

CREATE TABLE IF NOT EXISTS papers (
    id           BIGSERIAL PRIMARY KEY,
    exam         TEXT NOT NULL,
    year         INTEGER NOT NULL,
    subject      TEXT NOT NULL,
    session      TEXT NOT NULL DEFAULT '',
    title        TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    source_url   TEXT NOT NULL DEFAULT '',
    file_name    TEXT NOT NULL DEFAULT '',
    stored_name  TEXT NOT NULL DEFAULT '',   -- Supabase object path, or EXTERNAL_URL
    file_size    BIGINT NOT NULL DEFAULT 0,
    downloads    BIGINT NOT NULL DEFAULT 0,
    created_at   BIGINT NOT NULL,
    updated_at   BIGINT NOT NULL,
    -- Required by cbse_discovery.sync_cbse_papers(); not in app.py's INSERTs.
    class_name   TEXT NOT NULL DEFAULT '',
    subject_code TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS papers_exam_year_idx ON papers (exam, year DESC);
CREATE INDEX IF NOT EXISTS papers_source_url_idx ON papers (source_url);
-- Intentionally NOT UNIQUE: the shipped seed data reuses the same CISCE
-- landing-page URL for two rows. sync_cbse_papers() does a SELECT-then-INSERT,
-- so concurrent syncs can still race; see REVIEW.md.

CREATE TABLE IF NOT EXISTS mock_tests (
    id              BIGSERIAL PRIMARY KEY,
    exam            TEXT NOT NULL,
    subject         TEXT NOT NULL,
    question        TEXT NOT NULL,
    option_a        TEXT NOT NULL,
    option_b        TEXT NOT NULL,
    option_c        TEXT NOT NULL,
    option_d        TEXT NOT NULL,
    correct_option  TEXT NOT NULL,
    explanation     TEXT NOT NULL,
    official_source TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS mock_tests_exam_subject_idx ON mock_tests (exam, subject);

-- ---------------------------------------------------------------------------
-- Discovery tables: used only by *_discovery.py sync functions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sample_papers (
    id               BIGSERIAL PRIMARY KEY,
    exam             TEXT NOT NULL,
    class_name       TEXT NOT NULL,
    academic_session TEXT NOT NULL,
    subject          TEXT NOT NULL,
    document_type    TEXT NOT NULL,
    title            TEXT NOT NULL,
    source_url       TEXT NOT NULL,
    source_page      TEXT NOT NULL,
    created_at       BIGINT NOT NULL,
    updated_at       BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS sample_papers_source_url_idx ON sample_papers (source_url);

CREATE TABLE IF NOT EXISTS jee_main_papers (
    id                   BIGSERIAL PRIMARY KEY,
    year                 INTEGER NOT NULL,
    session_name         TEXT NOT NULL,
    exam_date            TEXT NOT NULL,
    shift                TEXT NOT NULL,
    paper_type           TEXT NOT NULL,
    language             TEXT NOT NULL,
    document_type        TEXT NOT NULL,
    title                TEXT NOT NULL,
    source_url           TEXT NOT NULL,
    source_page          TEXT NOT NULL,
    source_authority     TEXT NOT NULL,
    verification_status  TEXT NOT NULL,
    source_type          TEXT NOT NULL,
    source_label         TEXT NOT NULL,
    created_at           BIGINT NOT NULL,
    updated_at           BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS jee_main_papers_source_url_idx ON jee_main_papers (source_url);

CREATE TABLE IF NOT EXISTS jee_main_year_sources (
    id                   BIGSERIAL PRIMARY KEY,
    year                 INTEGER NOT NULL,
    source_url           TEXT NOT NULL,
    source_type          TEXT NOT NULL,
    source_label         TEXT NOT NULL,
    source_authority     TEXT NOT NULL,
    verification_status  TEXT NOT NULL,
    created_at           BIGINT NOT NULL,
    updated_at           BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS jee_main_year_sources_year_idx
    ON jee_main_year_sources (year);

CREATE TABLE IF NOT EXISTS jee_advanced_papers (
    id                    BIGSERIAL PRIMARY KEY,
    year                  INTEGER NOT NULL,
    exam_date             TEXT NOT NULL,
    paper_type            TEXT NOT NULL,
    language              TEXT NOT NULL,
    document_type         TEXT NOT NULL,
    title                 TEXT NOT NULL,
    source_url            TEXT NOT NULL UNIQUE,  -- required by ON CONFLICT
    source_page           TEXT NOT NULL,
    source_authority      TEXT NOT NULL,
    source_type           TEXT NOT NULL,
    source_label          TEXT NOT NULL,
    verification_status   TEXT NOT NULL,
    created_at            BIGINT NOT NULL,
    updated_at            BIGINT NOT NULL,
    exam_name             TEXT NOT NULL,
    stage                 TEXT NOT NULL,
    organizing_institute  TEXT NOT NULL,
    exam_session          TEXT NOT NULL,
    download_url          TEXT NOT NULL,
    storage_path          TEXT NOT NULL,
    download_mode         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS public.neet_papers (
    id                    BIGSERIAL PRIMARY KEY,
    year                  INTEGER NOT NULL,
    exam_date             TEXT NOT NULL,
    paper_type            TEXT NOT NULL,
    language              TEXT NOT NULL,
    document_type         TEXT NOT NULL,
    title                 TEXT NOT NULL,
    source_url            TEXT NOT NULL UNIQUE,  -- required by ON CONFLICT
    source_page           TEXT NOT NULL,
    source_authority      TEXT NOT NULL,
    source_type           TEXT NOT NULL,
    source_label          TEXT NOT NULL,
    verification_status   TEXT NOT NULL,
    created_at            BIGINT NOT NULL,
    updated_at            BIGINT NOT NULL,
    exam_name             TEXT NOT NULL,
    exam_session          TEXT NOT NULL,
    exam_code             TEXT NOT NULL,
    download_url          TEXT NOT NULL,
    storage_path          TEXT NOT NULL,
    download_mode         TEXT NOT NULL
);

-- ---------------------------------------------------------------------------
-- Supabase Storage (not SQL, but required at runtime)
-- ---------------------------------------------------------------------------
-- Create a bucket named by SUPABASE_BUCKET (default: edusphere-papers) and
-- make it PUBLIC, or get_public_url() will return a link that returns 401.
-- The service-role key must stay server-side only; never ship it to the
-- frontend.
