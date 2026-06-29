"""
models/user.py
==============
User model with role-based access control.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional


class UserRole(str, Enum):
    ADMIN   = "admin"
    STUDENT = "student"


@dataclass
class User:
    id:            str
    email:         str
    full_name:     str
    role:          UserRole
    is_active:     bool         = True
    last_login:    Optional[datetime] = None
    created_at:    Optional[datetime] = None

    # ── Convenience properties ──────────────────────────────
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def initials(self) -> str:
        parts = self.full_name.split()
        return "".join(p[0].upper() for p in parts[:2]) if parts else "?"

    @property
    def display_name(self) -> str:
        return self.full_name or self.email

    # ── Serialization ───────────────────────────────────────
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            id=data.get("id", ""),
            email=data.get("email", ""),
            full_name=data.get("full_name", ""),
            role=UserRole(data.get("role", "student")),
            is_active=data.get("is_active", True),
            last_login=data.get("last_login"),
            created_at=data.get("created_at"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
        }
