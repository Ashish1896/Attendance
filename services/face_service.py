"""
services/face_service.py  — Lightweight Edition
=================================================
Face detection and recognition using ONLY OpenCV + NumPy.
• No TensorFlow  • No dlib  • No DeepFace  • No downloads
• Works on Python 3.13 on Windows out of the box.

Algorithm:
  Detection  → OpenCV Haar Cascade (frontalface_default, built-in)
  Embedding  → 128-d block histogram descriptor
               Face crop → 64×64 grayscale → equalise → 4×4 grid
               → 8-bin histogram per cell → 16×8 = 128 values → L2 normalise
  Matching   → Euclidean distance on normalised vectors
               (equivalent to cosine distance; compatible with pgvector <->)

Threshold guidance (normalised L2):
  < 0.35  → confident match
  0.35–0.50 → possible match (lower threshold = stricter)
  > 0.50  → no match
"""

import io
import cv2
import logging
import numpy as np
from typing import Optional, List, Dict
from PIL import Image, ImageDraw

from database.supabase_client import get_db
from utils.constants import FACE_MATCH_THRESHOLD, FACE_EMBEDDING_DIM

logger = logging.getLogger(__name__)

# ── Haar Cascade (bundled with OpenCV, no download needed) ───
_cascade: Optional[cv2.CascadeClassifier] = None


def _get_cascade() -> cv2.CascadeClassifier:
    """Returns the cached Haar cascade classifier."""
    global _cascade
    if _cascade is None:
        import os
        # Try OpenCV's built-in data directory first
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if not os.path.exists(cascade_path):
            raise FileNotFoundError(
                f"Haar cascade not found at {cascade_path}. "
                "Reinstall opencv-python-headless."
            )
        _cascade = cv2.CascadeClassifier(cascade_path)
        logger.info(f"✅ Haar cascade loaded: {cascade_path}")
    return _cascade


# ──────────────────────────────────────────────────────────────
# Image helpers
# ──────────────────────────────────────────────────────────────
def bytes_to_image(image_bytes: bytes) -> Image.Image:
    """Converts raw bytes to a PIL Image."""
    return Image.open(io.BytesIO(image_bytes))


def _pil_to_cv2_gray(image: Image.Image) -> np.ndarray:
    """Converts PIL Image → OpenCV grayscale numpy array."""
    rgb = np.array(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)


def _pil_to_cv2_rgb(image: Image.Image) -> np.ndarray:
    """Converts PIL Image → OpenCV RGB numpy array."""
    return np.array(image.convert("RGB"))


# ──────────────────────────────────────────────────────────────
# Face Detection
# ──────────────────────────────────────────────────────────────
def detect_faces(image: Image.Image) -> List[Dict]:
    """
    Detects faces using OpenCV Haar Cascade.
    Returns list of dicts: {'facial_area': {'x','y','w','h'}, 'confidence': float}
    Compatible with draw_face_boxes() interface.
    """
    cascade = _get_cascade()
    gray    = _pil_to_cv2_gray(image)

    # Detect at multiple scales
    rects = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    if len(rects) == 0:
        return []

    faces = []
    for (x, y, w, h) in rects:
        faces.append({
            "facial_area": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
            "confidence":  0.9,   # Haar doesn't give a probability score
        })

    logger.debug(f"Detected {len(faces)} face(s)")
    return faces


def has_face(image: Image.Image) -> bool:
    """Returns True if at least one face detected."""
    return len(detect_faces(image)) > 0


def draw_face_boxes(image: Image.Image, faces: List[Dict]) -> Image.Image:
    """
    Draws green bounding boxes around detected faces.
    faces: list of dicts with 'facial_area' key → {x, y, w, h}
    """
    img  = image.copy().convert("RGBA")
    draw = ImageDraw.Draw(img)
    for face in faces:
        area = face.get("facial_area", {})
        x = area.get("x", 0)
        y = area.get("y", 0)
        w = area.get("w", 0)
        h = area.get("h", 0)
        if w > 0 and h > 0:
            # Outer box
            draw.rectangle([(x, y), (x + w, y + h)],
                           outline=(0, 212, 170), width=3)
            # Corner accents
            corner = 15
            for cx, cy in [(x, y), (x+w, y), (x, y+h), (x+w, y+h)]:
                draw.rectangle([(cx-2, cy-2), (cx+2, cy+2)],
                               fill=(0, 212, 170))
    return img.convert("RGB")


# ──────────────────────────────────────────────────────────────
# Embedding Generation
# ──────────────────────────────────────────────────────────────
def _compute_embedding(face_crop_gray: np.ndarray) -> np.ndarray:
    """
    Computes a 128-d descriptor from a grayscale face crop.

    Steps:
      1. Resize to 64×64
      2. CLAHE histogram equalisation (lighting invariant)
      3. Divide into 4×4 = 16 blocks (16×16 pixels each)
      4. 8-bin histogram per block → 128 values total
      5. L2 normalise → unit vector
    """
    # Resize
    face = cv2.resize(face_crop_gray, (64, 64), interpolation=cv2.INTER_AREA)

    # CLAHE — better than equalizeHist for local contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    face  = clahe.apply(face)

    # Block histogram
    blocks = []
    block_size = 16   # 64 / 4 = 16px per block
    for row in range(4):
        for col in range(4):
            block = face[
                row * block_size : (row + 1) * block_size,
                col * block_size : (col + 1) * block_size,
            ]
            hist, _ = np.histogram(block.ravel(), bins=8, range=(0, 256))
            blocks.append(hist.astype(np.float32))

    embedding = np.concatenate(blocks)   # shape: (128,)

    # L2 normalise
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    return embedding.astype(np.float32)


def _crop_face(image: Image.Image, face: Dict) -> Optional[np.ndarray]:
    """Crops a face region from the image and returns grayscale numpy array."""
    area = face.get("facial_area", {})
    x, y = area.get("x", 0), area.get("y", 0)
    w, h = area.get("w", 0), area.get("h", 0)
    if w <= 0 or h <= 0:
        return None

    gray = _pil_to_cv2_gray(image)
    # Slight padding for better embeddings
    pad  = int(min(w, h) * 0.1)
    ih, iw = gray.shape
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(iw, x + w + pad)
    y2 = min(ih, y + h + pad)
    return gray[y1:y2, x1:x2]


def get_face_encoding(image: Image.Image) -> Optional[np.ndarray]:
    """
    Returns 128-d embedding for the first detected face.
    Returns None if no face found.
    """
    faces = detect_faces(image)
    if not faces:
        logger.debug("get_face_encoding: no face detected")
        return None

    # Use the largest face (most prominent)
    faces_sorted = sorted(
        faces,
        key=lambda f: f["facial_area"]["w"] * f["facial_area"]["h"],
        reverse=True,
    )
    crop = _crop_face(image, faces_sorted[0])
    if crop is None or crop.size == 0:
        return None

    return _compute_embedding(crop)


def get_average_encoding(images: List[Image.Image]) -> Optional[np.ndarray]:
    """
    Computes the average 128-d embedding from multiple face images.
    Returns None if no faces found in any image.
    """
    encodings = []
    for i, img in enumerate(images):
        enc = get_face_encoding(img)
        if enc is not None:
            encodings.append(enc)
            logger.info(f"Encoded image {i+1}/{len(images)}")
        else:
            logger.warning(f"No face found in image {i+1}")

    if not encodings:
        return None

    avg  = np.mean(encodings, axis=0).astype(np.float32)
    norm = np.linalg.norm(avg)
    return avg / norm if norm > 0 else avg


# ──────────────────────────────────────────────────────────────
# Storage
# ──────────────────────────────────────────────────────────────
def save_face_embedding(student_id: str, embedding: np.ndarray, image_count: int) -> bool:
    """Saves the 128-d embedding to the student's Supabase record."""
    try:
        db = get_db()
        db.table("students").update({
            "face_embedding": embedding.tolist(),
            "face_images":    image_count,
        }).eq("id", student_id).execute()
        return True
    except Exception as exc:
        logger.error(f"save_face_embedding({student_id}): {exc}")
        return False


# ──────────────────────────────────────────────────────────────
# Matching
# ──────────────────────────────────────────────────────────────
def match_face_in_db(
    query_encoding: np.ndarray,
    threshold: float = FACE_MATCH_THRESHOLD,
) -> Optional[dict]:
    """
    Finds the closest student embedding in Supabase.
    Tries pgvector RPC first, falls back to in-memory search.
    """
    try:
        db  = get_db()
        res = db.rpc("match_face_embedding", {
            "query_embedding": query_encoding.tolist(),
            "match_threshold": threshold,
            "match_count":     1,
        }).execute()
        if res.data:
            match = res.data[0]
            dist  = float(match.get("distance", 1.0))
            match["confidence"] = round(max(0.0, 1.0 - dist), 4)
            return match
        return None
    except Exception as exc:
        logger.warning(f"pgvector RPC unavailable, using in-memory: {exc}")
        return _match_in_memory(query_encoding, threshold)


def _match_in_memory(
    query_encoding: np.ndarray,
    threshold: float,
) -> Optional[dict]:
    """
    Loads all embeddings from DB and does in-memory nearest-neighbour search.
    Fallback when pgvector RPC is not available.
    """
    try:
        db  = get_db()
        res = db.table("students").select(
            "id, name, roll_number, department, face_embedding"
        ).eq("is_active", True).not_.is_("face_embedding", "null").execute()

        if not res.data:
            return None

        known_encodings = []
        student_refs    = []
        for row in res.data:
            emb = row.get("face_embedding")
            if emb and len(emb) == FACE_EMBEDDING_DIM:
                arr  = np.array(emb, dtype=np.float32)
                norm = np.linalg.norm(arr)
                known_encodings.append(arr / norm if norm > 0 else arr)
                student_refs.append(row)

        if not known_encodings:
            return None

        known_matrix = np.stack(known_encodings)           # (N, 128)
        distances    = np.linalg.norm(known_matrix - query_encoding, axis=1)

        min_idx  = int(np.argmin(distances))
        min_dist = float(distances[min_idx])

        logger.info(f"Best match distance: {min_dist:.4f} (threshold: {threshold})")

        if min_dist < threshold:
            match = {k: v for k, v in student_refs[min_idx].items()
                     if k != "face_embedding"}
            match["student_id"] = match.pop("id", "")
            match["distance"]   = min_dist
            match["confidence"] = round(max(0.0, 1.0 - min_dist), 4)
            return match
        return None

    except Exception as exc:
        logger.error(f"_match_in_memory: {exc}")
        return None
