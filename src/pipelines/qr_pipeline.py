"""
QR Attendance Pipeline
----------------------
Generates rotating, signed QR tokens that expire after TOKEN_TTL_SECONDS.
Uses only Python's built-in `hmac` / `hashlib` — no extra dependencies.
"""

import hmac
import hashlib
import time
import io
import os

import segno
from PIL import Image

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
TOKEN_TTL_SECONDS = 20          # QR code lifetime
_SECRET = os.environ.get("QR_SECRET", "snapclass-qr-secret-key-2024")


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def _sign(payload: str) -> str:
    """Return a hex HMAC-SHA256 signature for *payload*."""
    return hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def generate_qr_token(subject_id: int) -> str:
    """
    Build a signed token string:
        <subject_id>:<unix_timestamp>:<signature>
    """
    ts = int(time.time())
    payload = f"{subject_id}:{ts}"
    sig = _sign(payload)
    return f"{payload}:{sig}"


def validate_qr_token(token: str) -> int | None:
    """
    Validate a token.
    Returns the subject_id (int) if valid and not expired, else None.
    """
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        subject_id_str, ts_str, sig = parts
        payload = f"{subject_id_str}:{ts_str}"

        # Verify signature (constant-time comparison)
        expected_sig = _sign(payload)
        if not hmac.compare_digest(sig, expected_sig):
            return None

        # Check expiry
        age = time.time() - int(ts_str)
        if age > TOKEN_TTL_SECONDS:
            return None

        return int(subject_id_str)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# QR image rendering
# ---------------------------------------------------------------------------

def make_qr_image(data: str, scale: int = 10) -> Image.Image:
    """
    Render *data* as a QR code and return a PIL Image.
    Uses segno with a dark-on-white palette.
    """
    qr = segno.make_qr(data, error="M")
    buf = io.BytesIO()
    qr.save(buf, kind="png", scale=scale, dark="#000000", light="#ffffff")
    buf.seek(0)
    return Image.open(buf).copy()
