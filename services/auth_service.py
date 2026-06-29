"""
services/auth_service.py
========================
Authentication service: login, signup, session management,
password hashing with bcrypt, role-based access control.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

import bcrypt
from dotenv import load_dotenv

from database.supabase_client import get_db
from models.user import User, UserRole
from utils.constants import SESSION_KEY
from utils.validators import validate_email, validate_password, ValidationError

load_dotenv()
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Password helpers
# ──────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Returns bcrypt hash of the password (cost=12)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Returns True if password matches the hash."""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────
# User CRUD
# ──────────────────────────────────────────────────────────────
def get_user_by_email(email: str) -> Optional[dict]:
    """Fetches a user record by email from Supabase."""
    try:
        db  = get_db()
        res = db.table("users").select("*").eq("email", email).single().execute()
        return res.data
    except Exception as exc:
        logger.debug(f"get_user_by_email({email}): {exc}")
        return None


def create_user(
    email: str,
    password: str,
    full_name: str,
    role: str = "student",
) -> Tuple[bool, str]:
    """
    Creates a new user.
    Returns (success: bool, message: str).
    """
    try:
        email     = validate_email(email)
        password  = validate_password(password)
        password_hash = hash_password(password)

        db  = get_db()
        db.table("users").insert({
            "email":         email,
            "password_hash": password_hash,
            "full_name":     full_name,
            "role":          role,
        }).execute()
        return True, "Account created successfully!"
    except ValidationError as exc:
        return False, str(exc)
    except Exception as exc:
        err = str(exc)
        if "duplicate" in err.lower() or "unique" in err.lower():
            return False, "An account with this email already exists."
        logger.error(f"create_user error: {exc}")
        return False, "Failed to create account. Please try again."


# ──────────────────────────────────────────────────────────────
# Login / Logout
# ──────────────────────────────────────────────────────────────
def login(email: str, password: str) -> Tuple[bool, str, Optional[dict]]:
    """
    Authenticates a user.
    Returns (success, message, user_dict or None).
    """
    try:
        email = validate_email(email)
    except ValidationError as exc:
        return False, str(exc), None

    user_data = get_user_by_email(email)
    if not user_data:
        return False, "No account found with this email.", None

    if not user_data.get("is_active", True):
        return False, "Your account is deactivated. Contact admin.", None

    if not verify_password(password, user_data.get("password_hash", "")):
        return False, "Incorrect password.", None

    # Update last_login timestamp
    try:
        get_db().table("users").update(
            {"last_login": datetime.now(timezone.utc).isoformat()}
        ).eq("id", user_data["id"]).execute()
    except Exception:
        pass

    session_user = {
        "id":        user_data["id"],
        "email":     user_data["email"],
        "full_name": user_data["full_name"],
        "role":      user_data["role"],
        "initials":  _initials(user_data["full_name"]),
    }
    return True, f"Welcome back, {user_data['full_name']}!", session_user


def _initials(name: str) -> str:
    parts = name.split()
    return "".join(p[0].upper() for p in parts[:2]) if parts else "?"


# ──────────────────────────────────────────────────────────────
# Bootstrap admin (called on first run)
# ──────────────────────────────────────────────────────────────
def bootstrap_admin() -> None:
    """Creates the default admin user if no admins exist."""
    admin_email    = os.getenv("ADMIN_EMAIL", "admin@school.edu")
    admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123456")
    admin_name     = os.getenv("ADMIN_NAME", "System Administrator")

    try:
        db  = get_db()
        res = db.table("users").select("id").eq("role", "admin").limit(1).execute()
        if res.data:
            return  # Admin already exists

        db.table("users").insert({
            "email":         admin_email,
            "password_hash": hash_password(admin_password),
            "full_name":     admin_name,
            "role":          "admin",
        }).execute()
        logger.info(f"✅ Bootstrap admin created: {admin_email}")
    except Exception as exc:
        logger.warning(f"Bootstrap admin skipped: {exc}")


# ──────────────────────────────────────────────────────────────
# Role helpers
# ──────────────────────────────────────────────────────────────
def is_admin(session_user: Optional[dict]) -> bool:
    return session_user is not None and session_user.get("role") == "admin"


def is_student(session_user: Optional[dict]) -> bool:
    return session_user is not None and session_user.get("role") == "student"
