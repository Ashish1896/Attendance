-- ============================================================
-- Smart Attendance System — Supabase Database Schema
-- Run this in your Supabase SQL Editor
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- TABLE: users (authentication & role management)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name   TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('admin', 'student')),
    is_active   BOOLEAN DEFAULT TRUE,
    last_login  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_role  ON public.users(role);

-- ============================================================
-- TABLE: students (student profiles + face embeddings)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.students (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id        UUID REFERENCES public.users(id) ON DELETE SET NULL,
    name           TEXT NOT NULL,
    email          TEXT UNIQUE NOT NULL,
    roll_number    TEXT UNIQUE NOT NULL,
    department     TEXT NOT NULL,
    phone          TEXT,
    face_embedding vector(128),         -- 128-d face_recognition encoding
    face_images    INTEGER DEFAULT 0,   -- count of uploaded face images
    qr_code_token  TEXT UNIQUE DEFAULT uuid_generate_v4()::text,
    qr_code_data   TEXT,               -- base64 encoded QR image
    photo_url      TEXT,
    is_active      BOOLEAN DEFAULT TRUE,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_students_roll     ON public.students(roll_number);
CREATE INDEX IF NOT EXISTS idx_students_dept     ON public.students(department);
CREATE INDEX IF NOT EXISTS idx_students_email    ON public.students(email);
-- Vector index for fast similarity search (HNSW for production scale)
CREATE INDEX IF NOT EXISTS idx_students_embedding
    ON public.students USING hnsw (face_embedding vector_l2_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================
-- TABLE: attendance (attendance records)
-- ============================================================
CREATE TABLE IF NOT EXISTS public.attendance (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id  UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    date        DATE NOT NULL DEFAULT CURRENT_DATE,
    time        TIME NOT NULL DEFAULT CURRENT_TIME,
    method      TEXT NOT NULL DEFAULT 'face' CHECK (method IN ('face', 'qr', 'manual')),
    status      TEXT NOT NULL DEFAULT 'present' CHECK (status IN ('present', 'absent', 'late')),
    confidence  FLOAT,                  -- face match confidence (0-1)
    marked_by   UUID REFERENCES public.users(id),
    notes       TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_attendance_student  ON public.attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date     ON public.attendance(date);
CREATE INDEX IF NOT EXISTS idx_attendance_status   ON public.attendance(status);
CREATE INDEX IF NOT EXISTS idx_attendance_method   ON public.attendance(method);

-- Unique constraint: one attendance record per student per day
CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_student_date
    ON public.attendance(student_id, date);

-- ============================================================
-- STORED FUNCTION: match_face_embedding
-- Finds the nearest student by L2 Euclidean distance
-- ============================================================
CREATE OR REPLACE FUNCTION public.match_face_embedding(
    query_embedding vector(128),
    match_threshold FLOAT DEFAULT 0.5,
    match_count     INT    DEFAULT 1
)
RETURNS TABLE (
    student_id  UUID,
    name        TEXT,
    roll_number TEXT,
    department  TEXT,
    distance    FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        s.id         AS student_id,
        s.name,
        s.roll_number,
        s.department,
        (s.face_embedding <-> query_embedding)::FLOAT AS distance
    FROM public.students s
    WHERE
        s.face_embedding IS NOT NULL
        AND s.is_active = TRUE
        AND (s.face_embedding <-> query_embedding) < match_threshold
    ORDER BY s.face_embedding <-> query_embedding
    LIMIT match_count;
$$;

-- ============================================================
-- STORED FUNCTION: get_attendance_stats
-- Returns daily attendance counts
-- ============================================================
CREATE OR REPLACE FUNCTION public.get_attendance_stats(target_date DATE DEFAULT CURRENT_DATE)
RETURNS TABLE (
    total_students  BIGINT,
    present_count   BIGINT,
    absent_count    BIGINT,
    attendance_pct  NUMERIC
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        (SELECT COUNT(*) FROM public.students WHERE is_active = TRUE) AS total_students,
        (SELECT COUNT(*) FROM public.attendance WHERE date = target_date AND status = 'present') AS present_count,
        (SELECT COUNT(*) FROM public.students WHERE is_active = TRUE) -
        (SELECT COUNT(*) FROM public.attendance WHERE date = target_date AND status = 'present') AS absent_count,
        CASE
            WHEN (SELECT COUNT(*) FROM public.students WHERE is_active = TRUE) = 0 THEN 0
            ELSE ROUND(
                (SELECT COUNT(*) FROM public.attendance WHERE date = target_date AND status = 'present')::NUMERIC /
                (SELECT COUNT(*) FROM public.students WHERE is_active = TRUE)::NUMERIC * 100, 2
            )
        END AS attendance_pct;
$$;

-- ============================================================
-- TRIGGERS: auto-update updated_at timestamp
-- ============================================================
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_users_updated
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE OR REPLACE TRIGGER trg_students_updated
    BEFORE UPDATE ON public.students
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================
ALTER TABLE public.users      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.students   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance ENABLE ROW LEVEL SECURITY;

-- Using service_role key bypasses RLS, which is what our backend uses
-- These policies allow anon read for demo (tighten in production)
CREATE POLICY "Service role has full access to users"
    ON public.users FOR ALL USING (TRUE);

CREATE POLICY "Service role has full access to students"
    ON public.students FOR ALL USING (TRUE);

CREATE POLICY "Service role has full access to attendance"
    ON public.attendance FOR ALL USING (TRUE);

-- ============================================================
-- VIEWS: Convenience views for reporting
-- ============================================================
CREATE OR REPLACE VIEW public.v_attendance_detail AS
SELECT
    a.id,
    a.date,
    a.time,
    a.method,
    a.status,
    a.confidence,
    a.created_at,
    s.name        AS student_name,
    s.roll_number,
    s.department,
    s.email       AS student_email
FROM public.attendance a
JOIN public.students s ON s.id = a.student_id;

CREATE OR REPLACE VIEW public.v_student_attendance_summary AS
SELECT
    s.id,
    s.name,
    s.roll_number,
    s.department,
    s.email,
    COUNT(a.id)                                           AS total_present,
    ROUND(COUNT(a.id)::NUMERIC /
        NULLIF((SELECT COUNT(DISTINCT date) FROM public.attendance), 0) * 100, 2) AS attendance_pct
FROM public.students s
LEFT JOIN public.attendance a ON a.student_id = s.id AND a.status = 'present'
WHERE s.is_active = TRUE
GROUP BY s.id, s.name, s.roll_number, s.department, s.email;
