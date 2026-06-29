import numpy as np
import streamlit as st

try:
    import dlib
    import face_recognition_models
    from sklearn.svm import SVC
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

from src.database.db import get_all_students


@st.cache_resource
def load_dlib_models():
    if not FACE_RECOGNITION_AVAILABLE:
        return None, None, None
    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )
    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )
    return detector, sp, facerec


def get_face_embeddings(image_np):
    if not FACE_RECOGNITION_AVAILABLE:
        return []
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1)
    encodings = []
    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        encodings.append(np.array(face_descriptor))
    return encodings


def _build_model():
    """
    Build and return the SVM classifier from the current student DB.
    Not cached — always reads latest data from DB.
    Use get_trained_model() which caches per-session after training.
    """
    if not FACE_RECOGNITION_AVAILABLE:
        return None

    X = []
    y = []

    student_db = get_all_students()
    if not student_db:
        return None

    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            X.append(np.array(embedding))
            y.append(student.get('student_id'))

    if len(X) == 0:
        return None

    clf = SVC(kernel='linear', probability=True, class_weight='balanced')
    try:
        clf.fit(X, y)
    except ValueError:
        return None

    return {'clf': clf, 'X': X, 'y': y, 'all_students': sorted(set(y))}


def train_classifier() -> bool:
    """
    Force a model rebuild and store it in session_state so this session
    immediately uses the updated model (which includes the newly registered student).
    """
    model_data = _build_model()
    st.session_state['trained_model'] = model_data
    return bool(model_data)


def _get_model():
    """
    Return model from session_state if already built this session,
    otherwise build it fresh from DB (happens once per session).
    """
    if 'trained_model' not in st.session_state:
        st.session_state['trained_model'] = _build_model()
    return st.session_state['trained_model']


def predict_attendance(class_image_np: np.ndarray):
    if not FACE_RECOGNITION_AVAILABLE:
        st.warning("Face recognition libraries are not installed on this system.")
        return {}, [], 0

    encodings = get_face_embeddings(class_image_np)
    detected_student = {}

    model_data = _get_model()

    if not model_data:
        # No students registered yet
        return detected_student, [], len(encodings)

    clf = model_data['clf']
    X_train = model_data['X']
    y_train = model_data['y']
    all_students = model_data['all_students']

    for encoding in encodings:
        if len(all_students) >= 2:
            predicted_id = int(clf.predict([encoding])[0])
        else:
            predicted_id = int(all_students[0])

        student_indices = [i for i, y in enumerate(y_train) if y == predicted_id]
        student_embeddings = np.array([X_train[i] for i in student_indices])
        mean_embedding = student_embeddings.mean(axis=0)
        best_match_score = np.linalg.norm(mean_embedding - encoding)

        if best_match_score <= 0.6:
            detected_student[predicted_id] = True

    return detected_student, all_students, len(encodings)
