"""
models/attendance.py
====================
Attendance model with method and status enums.
"""

from dataclasses import dataclass
from enum import Enum
from datetime import date, time, datetime
from typing import Optional


class AttendanceMethod(str, Enum):
    FACE   = "face"
    QR     = "qr"
    MANUAL = "manual"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT  = "absent"
    LATE    = "late"


@dataclass
class AttendanceRecord:
    id:           str
    student_id:   str
    date:         date
    time:         time
    method:       AttendanceMethod
    status:       AttendanceStatus
    confidence:   Optional[float]  = None   # face match confidence
    marked_by:    Optional[str]    = None
    notes:        Optional[str]    = None
    created_at:   Optional[datetime] = None

    # Optional joined fields (from views)
    student_name: Optional[str]    = None
    roll_number:  Optional[str]    = None
    department:   Optional[str]    = None
    student_email: Optional[str]   = None

    @property
    def is_present(self) -> bool:
        return self.status == AttendanceStatus.PRESENT

    @property
    def method_icon(self) -> str:
        icons = {
            AttendanceMethod.FACE:   "📷",
            AttendanceMethod.QR:     "📱",
            AttendanceMethod.MANUAL: "✍️",
        }
        return icons.get(self.method, "❓")

    @property
    def status_icon(self) -> str:
        icons = {
            AttendanceStatus.PRESENT: "✅",
            AttendanceStatus.ABSENT:  "❌",
            AttendanceStatus.LATE:    "⏰",
        }
        return icons.get(self.status, "❓")

    @classmethod
    def from_dict(cls, data: dict) -> "AttendanceRecord":
        return cls(
            id=data.get("id", ""),
            student_id=data.get("student_id", ""),
            date=data.get("date"),
            time=data.get("time"),
            method=AttendanceMethod(data.get("method", "face")),
            status=AttendanceStatus(data.get("status", "present")),
            confidence=data.get("confidence"),
            marked_by=data.get("marked_by"),
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            student_name=data.get("student_name"),
            roll_number=data.get("roll_number"),
            department=data.get("department"),
            student_email=data.get("student_email"),
        )
