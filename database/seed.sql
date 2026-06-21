-- ============================================================
-- Smart Attendance System — Seed Data
-- Run AFTER schema.sql
-- Provides sample admin + demo students for testing
-- ============================================================

-- ============================================================
-- ADMIN USER
-- Email: admin@school.edu
-- Password: Admin@123456 (bcrypt hash below)
-- ============================================================
INSERT INTO public.users (email, password_hash, full_name, role)
VALUES (
    'admin@school.edu',
    -- bcrypt hash of 'Admin@123456' (cost=12)
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBzG4.ByHGkQ7.',
    'System Administrator',
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- DEMO STUDENTS
-- ============================================================
INSERT INTO public.students (name, email, roll_number, department, phone) VALUES
    ('Aarav Sharma',   'aarav.sharma@student.edu',   'CS2021001', 'Computer Science', '+91-9876543210'),
    ('Priya Patel',    'priya.patel@student.edu',    'EC2021002', 'Electronics',      '+91-9876543211'),
    ('Rahul Kumar',    'rahul.kumar@student.edu',    'ME2021003', 'Mechanical',       '+91-9876543212'),
    ('Sneha Reddy',    'sneha.reddy@student.edu',    'CS2021004', 'Computer Science', '+91-9876543213'),
    ('Arjun Singh',    'arjun.singh@student.edu',    'CE2021005', 'Civil',            '+91-9876543214'),
    ('Kavya Nair',     'kavya.nair@student.edu',     'IT2021006', 'Information Tech', '+91-9876543215'),
    ('Dev Gupta',      'dev.gupta@student.edu',      'CS2021007', 'Computer Science', '+91-9876543216'),
    ('Meera Joshi',    'meera.joshi@student.edu',    'EC2021008', 'Electronics',      '+91-9876543217'),
    ('Vikram Mehta',   'vikram.mehta@student.edu',   'ME2021009', 'Mechanical',       '+91-9876543218'),
    ('Aisha Khan',     'aisha.khan@student.edu',     'IT2021010', 'Information Tech', '+91-9876543219')
ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- SAMPLE ATTENDANCE (last 7 days)
-- ============================================================
DO $$
DECLARE
    s   RECORD;
    d   DATE;
    rnd FLOAT;
BEGIN
    FOR s IN SELECT id FROM public.students LOOP
        FOR d IN SELECT generate_series(
            CURRENT_DATE - INTERVAL '6 days',
            CURRENT_DATE - INTERVAL '1 day',
            INTERVAL '1 day'
        )::DATE LOOP
            rnd := random();
            IF rnd > 0.2 THEN  -- 80% attendance rate
                INSERT INTO public.attendance (student_id, date, time, method, status)
                VALUES (
                    s.id,
                    d,
                    (TIME '08:00:00' + (random() * INTERVAL '2 hours'))::TIME,
                    CASE WHEN random() > 0.3 THEN 'face' ELSE 'qr' END,
                    'present'
                ) ON CONFLICT (student_id, date) DO NOTHING;
            END IF;
        END LOOP;
    END LOOP;
END $$;
