"""
utils/constants.py
==================
App-wide constants and configuration values.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── App Info ─────────────────────────────────────────────────
APP_NAME        = os.getenv("APP_NAME", "Smart Attendance System")
APP_VERSION     = "1.0.0"
APP_ICON        = "🎓"

# ── Face Recognition ─────────────────────────────────────────
FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.40"))
MIN_FACE_IMAGES      = 3
MAX_FACE_IMAGES      = 10
FACE_EMBEDDING_DIM   = 128

# ── Departments ──────────────────────────────────────────────
DEPARTMENTS = [
    "Computer Science",
    "Information Technology",
    "Electronics",
    "Electrical",
    "Mechanical",
    "Civil",
    "Chemical",
    "Biotechnology",
    "Physics",
    "Mathematics",
    "MBA",
    "Other",
]

# ── Date / Time ──────────────────────────────────────────────
DATE_FORMAT      = "%Y-%m-%d"
TIME_FORMAT      = "%H:%M:%S"
DISPLAY_DATE_FMT = "%d %b %Y"
DISPLAY_TIME_FMT = "%I:%M %p"

# ── Attendance ───────────────────────────────────────────────
ATTENDANCE_METHODS  = ["face", "qr", "manual"]
ATTENDANCE_STATUSES = ["present", "absent", "late"]

# ── Auth ─────────────────────────────────────────────────────
JWT_ALGORITHM    = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
SESSION_KEY      = "auth_user"

# ── UI ───────────────────────────────────────────────────────
SIDEBAR_LOGO = f"{APP_ICON} {APP_NAME}"
PAGE_ICON    = APP_ICON

# ── Colors (matching CSS variables) ──────────────────────────
COLOR_PRIMARY   = "#6C63FF"
COLOR_SECONDARY = "#00D4AA"
COLOR_SUCCESS   = "#4CAF50"
COLOR_DANGER    = "#FF4757"
COLOR_WARNING   = "#FFB347"
COLOR_MUTED     = "#9999BB"

PLOTLY_TEMPLATE = "plotly_dark"
PLOTLY_COLORS   = [
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_SUCCESS,
    COLOR_WARNING, COLOR_DANGER, "#FF6B9D", "#C77DFF",
]
