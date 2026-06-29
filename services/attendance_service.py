"""
services/attendance_service.py
================================
Attendance CRUD operations with duplicate prevention.
"""

import logging
from datetime import date, datetime, timezone
from typing import Optional, List, Tuple

from database.supabase_client import get_db
from models.attendance import AttendanceMethod, AttendanceStatus

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Core Marking
# ──────────────────────────────────────────────────────────────
def mark_attendance(
    student_id:  str,
    method:      str = "face",
    status:      str = "present",
    confidence:  Optional[float] = None,
    marked_by:   Optional[str]   = None,
    notes:       Optional[str]   = None,
    target_date: Optional[date]  = None,
) -> Tuple[bool, str]:
    """
    Marks attendance for a student.
    Prevents duplicates: one record per student per day.
    Returns (success, message).
    """
    today = target_date or date.today()

    # ── Duplicate check ──────────────────────────────────────
    existing = get_attendance_for_student_date(student_id, today)
    if existing:
        existing_time = existing.get("time", "")
        return False, (
            f"Attendance already marked for today at {existing_time}. "
            f"Method: {existing.get('method', 'unknown')}"
        )

    try:
        db  = get_db()
        now = datetime.now(timezone.utc)
        db.table("attendance").insert({
            "student_id": student_id,
            "date":       today.isoformat(),
            "time":       now.strftime("%H:%M:%S"),
            "method":     method,
            "status":     status,
            "confidence": confidence,
            "marked_by":  marked_by,
            "notes":      notes,
        }).execute()
        return True, f"✅ Attendance marked as {status} via {method}."
    except Exception as exc:
        err = str(exc)
        if "unique" in err.lower() or "duplicate" in err.lower():
            return False, "Attendance already recorded for today."
        logger.error(f"mark_attendance error: {exc}")
        return False, f"Failed to mark attendance: {exc}"


# ──────────────────────────────────────────────────────────────
# Read Operations
# ──────────────────────────────────────────────────────────────
def get_attendance_for_student_date(student_id: str, target_date: date) -> Optional[dict]:
    """Returns existing attendance record for a student on a date."""
    try:
        db  = get_db()
        res = db.table("attendance").select("*").eq(
            "student_id", student_id
        ).eq("date", target_date.isoformat()).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception as exc:
        logger.error(f"get_attendance_for_student_date: {exc}")
        return None


def get_today_attendance() -> List[dict]:
    """Returns all attendance records for today."""
    try:
        db  = get_db()
        res = db.table("v_attendance_detail").select("*").eq(
            "date", date.today().isoformat()
        ).order("time", desc=True).execute()
        return res.data or []
    except Exception as exc:
        logger.error(f"get_today_attendance: {exc}")
        return []


def get_attendance_range(
    start_date: date,
    end_date:   date,
    student_id: Optional[str] = None,
    department: Optional[str] = None,
) -> List[dict]:
    """Returns attendance records filtered by date range + optional filters."""
    try:
        db    = get_db()
        query = db.table("v_attendance_detail").select("*") \
            .gte("date", start_date.isoformat()) \
            .lte("date", end_date.isoformat()) \
            .order("date", desc=True).order("time", desc=True)

        if student_id:
            query = query.eq("student_id", student_id)
        if department:
            query = query.eq("department", department)

        res = query.execute()
        return res.data or []
    except Exception as exc:
        logger.error(f"get_attendance_range: {exc}")
        return []


def get_all_attendance() -> List[dict]:
    """Returns all attendance records (admin use)."""
    try:
        db  = get_db()
        res = db.table("v_attendance_detail").select("*").order("date", desc=True).execute()
        return res.data or []
    except Exception as exc:
        logger.error(f"get_all_attendance: {exc}")
        return []


# ──────────────────────────────────────────────────────────────
# Stats
# ──────────────────────────────────────────────────────────────
def get_today_stats() -> dict:
    """Returns today's attendance statistics."""
    try:
        db  = get_db()
        res = db.rpc("get_attendance_stats", {"target_date": date.today().isoformat()}).execute()
        return res.data[0] if res.data else _empty_stats()
    except Exception as exc:
        logger.warning(f"get_today_stats RPC failed, computing manually: {exc}")
        return _compute_stats_manually()


def _empty_stats() -> dict:
    return {"total_students": 0, "present_count": 0, "absent_count": 0, "attendance_pct": 0.0}


def _compute_stats_manually() -> dict:
    try:
        db = get_db()
        total_res   = db.table("students").select("id", count="exact").eq("is_active", True).execute()
        present_res = db.table("attendance").select("id", count="exact").eq(
            "date", date.today().isoformat()
        ).eq("status", "present").execute()

        total   = total_res.count or 0
        present = present_res.count or 0
        absent  = max(0, total - present)
        pct     = round(present / total * 100, 2) if total else 0.0
        return {"total_students": total, "present_count": present, "absent_count": absent, "attendance_pct": pct}
    except Exception as exc:
        logger.error(f"_compute_stats_manually: {exc}")
        return _empty_stats()


# ──────────────────────────────────────────────────────────────
# Student Management
# ──────────────────────────────────────────────────────────────
def get_all_students() -> List[dict]:
    """Returns all active students."""
    try:
        db  = get_db()
        res = db.table("students").select(
            "id, name, email, roll_number, department, phone, "
            "face_images, qr_code_token, is_active, created_at"
        ).eq("is_active", True).order("name").execute()
        return res.data or []
    except Exception as exc:
        logger.error(f"get_all_students: {exc}")
        return []


def get_student_by_id(student_id: str) -> Optional[dict]:
    try:
        db  = get_db()
        res = db.table("students").select("*").eq("id", student_id).single().execute()
        return res.data
    except Exception:
        return None


def create_student(data: dict) -> Tuple[bool, str, Optional[str]]:
    """Creates a student. Returns (success, message, new_id)."""
    try:
        db  = get_db()
        res = db.table("students").insert(data).execute()
        new_id = res.data[0]["id"] if res.data else None
        return True, "Student added successfully!", new_id
    except Exception as exc:
        err = str(exc)
        if "unique" in err.lower() or "duplicate" in err.lower():
            return False, "A student with this email or roll number already exists.", None
        logger.error(f"create_student: {exc}")
        return False, f"Failed to add student: {exc}", None


def update_student(student_id: str, data: dict) -> Tuple[bool, str]:
    try:
        db = get_db()
        db.table("students").update(data).eq("id", student_id).execute()
        return True, "Student updated successfully!"
    except Exception as exc:
        logger.error(f"update_student: {exc}")
        return False, f"Update failed: {exc}"


def delete_student(student_id: str) -> Tuple[bool, str]:
    """Soft-deletes a student (sets is_active=False)."""
    try:
        db = get_db()
        db.table("students").update({"is_active": False}).eq("id", student_id).execute()
        return True, "Student removed successfully."
    except Exception as exc:
        logger.error(f"delete_student: {exc}")
        return False, f"Delete failed: {exc}"


def get_student_summary() -> List[dict]:
    """Returns student attendance summary from view."""
    try:
        db  = get_db()
        res = db.table("v_student_attendance_summary").select("*").order("name").execute()
        return res.data or []
    except Exception as exc:
        logger.error(f"get_student_summary: {exc}")
        return []
