"""
models/student.py
=================
Student model with face embedding and QR code support.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import numpy as np


@dataclass
class Student:
    id:             str
    name:           str
    email:          str
    roll_number:    str
    department:     str
    phone:          Optional[str]   = None
    face_embedding: Optional[List[float]] = None   # 128-d vector
    face_images:    int             = 0
    qr_code_token:  Optional[str]   = None
    qr_code_data:   Optional[str]   = None          # base64 QR image
    photo_url:      Optional[str]   = None
    is_active:      bool            = True
    user_id:        Optional[str]   = None
    created_at:     Optional[datetime] = None
    updated_at:     Optional[datetime] = None

    # ── Convenience properties ──────────────────────────────
    @property
    def has_face(self) -> bool:
        return self.face_embedding is not None and len(self.face_embedding) == 128

    @property
    def has_qr(self) -> bool:
        return self.qr_code_data is not None

    @property
    def embedding_array(self) -> Optional[np.ndarray]:
        if self.face_embedding:
            return np.array(self.face_embedding)
        return None

    @property
    def initials(self) -> str:
        parts = self.name.split()
        return "".join(p[0].upper() for p in parts[:2]) if parts else "?"

    # ── Serialization ───────────────────────────────────────
    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        embedding = data.get("face_embedding")
        if isinstance(embedding, str):
            import json
            try:
                embedding = json.loads(embedding)
            except Exception:
                embedding = None

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            email=data.get("email", ""),
            roll_number=data.get("roll_number", ""),
            department=data.get("department", ""),
            phone=data.get("phone"),
            face_embedding=embedding,
            face_images=data.get("face_images", 0),
            qr_code_token=data.get("qr_code_token"),
            qr_code_data=data.get("qr_code_data"),
            photo_url=data.get("photo_url"),
            is_active=data.get("is_active", True),
            user_id=data.get("user_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "roll_number": self.roll_number,
            "department": self.department,
            "phone": self.phone,
            "face_images": self.face_images,
            "is_active": self.is_active,
        }
