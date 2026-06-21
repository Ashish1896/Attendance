"""
utils/validators.py
===================
Input validation and sanitization helpers.
All database queries use parameterized Supabase client calls,
which inherently protect against SQL injection.
"""

import re
import html
from typing import Optional


class ValidationError(Exception):
    """Raised when validation fails."""


# ── Email ────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

def validate_email(email: str) -> str:
    """Returns cleaned email or raises ValidationError."""
    email = email.strip().lower()
    if not email:
        raise ValidationError("Email is required.")
    if len(email) > 254:
        raise ValidationError("Email is too long.")
    if not EMAIL_REGEX.match(email):
        raise ValidationError(f"Invalid email format: {email}")
    return email


# ── Roll Number ──────────────────────────────────────────────
ROLL_REGEX = re.compile(r"^[A-Za-z0-9]+$")

def validate_roll_number(roll: str) -> str:
    """Returns cleaned roll number or raises ValidationError."""
    roll = roll.strip().upper()
    if not roll:
        raise ValidationError("Roll number is required.")
    if len(roll) < 3 or len(roll) > 20:
        raise ValidationError("Roll number must be 3–20 characters.")
    if not ROLL_REGEX.match(roll):
        raise ValidationError("Roll number must be alphanumeric only.")
    return roll


# ── Name ─────────────────────────────────────────────────────
NAME_REGEX = re.compile(r"^[A-Za-z\s\.\-']+$")

def validate_name(name: str) -> str:
    """Returns cleaned name or raises ValidationError."""
    name = name.strip()
    if not name:
        raise ValidationError("Name is required.")
    if len(name) < 2 or len(name) > 100:
        raise ValidationError("Name must be 2–100 characters.")
    if not NAME_REGEX.match(name):
        raise ValidationError("Name contains invalid characters.")
    return name


# ── Phone ─────────────────────────────────────────────────────
PHONE_REGEX = re.compile(r"^\+?[0-9\-\s\(\)]{7,20}$")

def validate_phone(phone: Optional[str]) -> Optional[str]:
    """Returns cleaned phone or None if empty, raises on bad format."""
    if not phone or not phone.strip():
        return None
    phone = phone.strip()
    if not PHONE_REGEX.match(phone):
        raise ValidationError("Invalid phone number format.")
    return phone


# ── Password ─────────────────────────────────────────────────
def validate_password(password: str) -> str:
    """Enforces minimum password strength."""
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one digit.")
    return password


# ── Generic string sanitizer ─────────────────────────────────
def sanitize_string(value: str, max_length: int = 255) -> str:
    """Escapes HTML and truncates to max_length."""
    return html.escape(value.strip())[:max_length]
