from src.database.config import supabase
from typing import Optional
import bcrypt



def hash_pass(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_pass(pwd: str, hashed: str) -> bool:
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


def check_teacher_exists(username: str) -> bool:
    # Check for unique username, returns True when username is already taken
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0



def create_teacher(username: str, password: str, name: str) -> list:
    data = {"username": username, "password": hash_pass(password), "name": name}
    response = supabase.table("teachers").insert(data).execute()
    return response.data


def teacher_login(username: str, password: str) -> Optional[dict]:
    # Only fetch non-sensitive fields after verifying password
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            # Strip the password hash before storing in session
            teacher.pop('password', None)
            return teacher
    return None


def get_all_students() -> list:
    response = supabase.table('students').select("*").execute()
    return response.data

def get_student_by_id(student_id: int) -> Optional[dict]:
    """Fetch a single student by ID — avoids loading the full table."""
    response = supabase.table('students').select("*").eq('student_id', student_id).execute()
    return response.data[0] if response.data else None

def create_student(new_name: str, face_embedding=None, voice_embedding=None) -> list:
    data = {'name': new_name, 'face_embedding': face_embedding, 'voice_embedding': voice_embedding}
    response = supabase.table('students').insert(data).execute()
    return response.data


def create_subject(subject_code, name, section, teacher_id):
    data = {"subject_code": subject_code, "name": name, "section": section, "teacher_id": teacher_id}
    response = supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subjects(teacher_id):
    response = supabase.table('subjects').select("*, subject_students(count), attendance_logs(timestamp)").eq("teacher_id", teacher_id).execute()
    subjects = response.data


    for sub in subjects:
        sub['total_students'] = sub.get("subject_students", [{}])[0].get('count', 0) if sub.get('subject_students') else 0
        attendance = sub.get('attendance_logs', [])
        unique_sessions = len(set(log['timestamp'] for log in attendance))
        sub['total_classes'] = unique_sessions


        sub.pop('subject_students', None)
        sub.pop('attendance_logs', None)

    return subjects


def enroll_student_to_subject(student_id: int, subject_id: int) -> list:
    data = {'student_id': student_id, 'subject_id': subject_id}
    response = supabase.table('subject_students').insert(data).execute()
    return response.data


def unenroll_student_to_subject(student_id: int, subject_id: int) -> list:
    response = supabase.table('subject_students').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()
    return response.data


def get_enrolled_students_with_details(subject_id: int) -> list:
    """Fetch enrolled students with their full profile for a given subject."""
    res = supabase.table('subject_students').select("*, students(*)").eq('subject_id', subject_id).execute()
    return res.data


def get_subject_by_code(subject_code: str) -> Optional[dict]:
    """Look up a subject by its join code. Returns None if not found."""
    res = supabase.table('subjects').select('subject_id, name, subject_code').ilike('subject_code', subject_code).execute()
    return res.data[0] if res.data else None


def check_enrollment(student_id: int, subject_id: int) -> bool:
    """Returns True if the student is already enrolled in the subject."""
    res = supabase.table('subject_students').select('student_id').eq('subject_id', subject_id).eq('student_id', student_id).execute()
    return bool(res.data)



def get_student_subjects(student_id):
    response = supabase.table('subject_students').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def get_student_attendance(student_id):
    response = supabase.table('attendance_logs').select('*, subjects(*)').eq('student_id', student_id).execute()
    return response.data


def create_attendance(logs):
    response = supabase.table('attendance_logs').insert(logs).execute()
    return response.data

def get_attendance_for_teacher(teacher_id):
    response = supabase.table('attendance_logs').select("*, subjects!inner(*), students(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data


def log_single_attendance(student_id: int, subject_id: int, timestamp: str) -> list:
    """Insert a single attendance record marking the student as present."""
    data = {
        'student_id': student_id,
        'subject_id': subject_id,
        'timestamp': timestamp,
        'is_present': True,
    }
    response = supabase.table('attendance_logs').insert(data).execute()
    return response.data
