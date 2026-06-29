"""
services/qr_service.py
======================
QR code generation and validation for student attendance backup.
Uses 'segno' for high-quality QR generation.
"""

import io
import base64
import logging
import uuid
from typing import Optional, Tuple

import segno
from PIL import Image

from database.supabase_client import get_db

logger = logging.getLogger(__name__)

QR_PREFIX = "ATTENDANCE_QR"


# ──────────────────────────────────────────────────────────────
# QR Generation
# ──────────────────────────────────────────────────────────────
def generate_qr_code(student_id: str, token: str) -> Tuple[str, str]:
    """
    Generates a QR code for a student.
    Returns (qr_data_uri: str, token: str).

    The QR encodes: "ATTENDANCE_QR|<student_id>|<token>"
    """
    payload = f"{QR_PREFIX}|{student_id}|{token}"

    qr = segno.make_qr(payload, error="H")
    buf = io.BytesIO()
    qr.save(
        buf,
        kind="png",
        scale=10,
        border=4,
        dark="#6C63FF",
        light="#FFFFFF",
    )
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    data_uri = f"data:image/png;base64,{b64}"
    return data_uri, token


def generate_and_save_qr(student_id: str) -> Tuple[bool, str]:
    """
    Generates a new QR code and saves it to the student record.
    Returns (success, message).
    """
    try:
        db  = get_db()
        res = db.table("students").select("qr_code_token").eq("id", student_id).single().execute()
        token = res.data.get("qr_code_token") or str(uuid.uuid4())

        data_uri, token = generate_qr_code(student_id, token)

        db.table("students").update({
            "qr_code_data":  data_uri,
            "qr_code_token": token,
        }).eq("id", student_id).execute()

        return True, "QR code generated successfully!"
    except Exception as exc:
        logger.error(f"generate_and_save_qr({student_id}): {exc}")
        return False, f"QR generation failed: {exc}"


def get_student_qr(student_id: str) -> Optional[str]:
    """Returns the base64 QR data URI for a student, or None."""
    try:
        db  = get_db()
        res = db.table("students").select("qr_code_data").eq("id", student_id).single().execute()
        return res.data.get("qr_code_data")
    except Exception:
        return None


# ──────────────────────────────────────────────────────────────
# QR Validation
# ──────────────────────────────────────────────────────────────
def validate_qr_token(raw_text: str) -> Optional[dict]:
    """
    Parses and validates a scanned QR code payload.
    Returns student dict if valid, None otherwise.

    Expected format: "ATTENDANCE_QR|<student_id>|<token>"
    """
    if not raw_text or not raw_text.startswith(QR_PREFIX):
        logger.warning(f"Invalid QR prefix: {raw_text[:50]}")
        return None

    parts = raw_text.split("|")
    if len(parts) != 3:
        logger.warning(f"Malformed QR payload: {raw_text[:80]}")
        return None

    _, student_id, token = parts
    try:
        db  = get_db()
        res = db.table("students").select(
            "id, name, roll_number, department, email, qr_code_token, is_active"
        ).eq("id", student_id).single().execute()
        student = res.data

        if not student:
            return None
        if not student.get("is_active", True):
            return None
        if student.get("qr_code_token") != token:
            logger.warning(f"Token mismatch for student {student_id}")
            return None

        return student
    except Exception as exc:
        logger.error(f"validate_qr_token error: {exc}")
        return None
