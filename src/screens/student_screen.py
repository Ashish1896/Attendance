import time
from datetime import datetime

import streamlit as st
from PIL import Image
import numpy as np

from src.ui.style_base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.pipelines.face_pipeline import predict_attendance, get_face_embeddings, train_classifier
from src.database.db import (
    get_all_students, create_student, get_student_subjects,
    get_student_attendance, unenroll_student_to_subject,
    get_student_by_id, log_single_attendance
)
from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card
from src.pipelines.qr_pipeline import validate_qr_token


# ---------------------------------------------------------------------------
# "Attendance Recorded" success animation
# ---------------------------------------------------------------------------

def _show_done_animation(subject_id: int):
    """Full-page success overlay shown after a QR scan records attendance."""
    st.markdown(
        """
        <style>
        @keyframes popIn {
            0%   { transform: scale(0.4); opacity: 0; }
            70%  { transform: scale(1.15); opacity: 1; }
            100% { transform: scale(1); }
        }
        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(20px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes confettiFall {
            0%   { transform: translateY(-10px) rotate(0deg); opacity: 1; }
            100% { transform: translateY(110vh) rotate(720deg); opacity: 0; }
        }

        .done-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 60vh;
            gap: 1.2rem;
        }
        .done-circle {
            width: 140px;
            height: 140px;
            background: linear-gradient(135deg, #43e97b, #38f9d7);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: popIn 0.6s cubic-bezier(0.36, 0.07, 0.19, 0.97) forwards;
            box-shadow: 0 0 60px rgba(67,233,123,0.45);
        }
        .done-check {
            font-size: 4rem;
            line-height: 1;
        }
        .done-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #1a1a2e;
            animation: fadeSlideUp 0.5s 0.4s both;
            text-align: center;
        }
        .done-sub {
            font-size: 1.1rem;
            color: #555;
            animation: fadeSlideUp 0.5s 0.6s both;
            text-align: center;
        }

        /* Confetti pieces */
        .confetti-piece {
            position: fixed;
            width: 12px;
            height: 12px;
            border-radius: 2px;
            animation: confettiFall linear forwards;
            opacity: 0;
        }
        </style>

        <div class="done-wrapper">
            <div class="done-circle">
                <span class="done-check">✓</span>
            </div>
            <div class="done-title">Attendance Recorded!</div>
            <div class="done-sub">You're marked <strong>present</strong> for today's class 🎉</div>
        </div>

        <!-- Confetti burst -->
        <script>
        (function() {
            const colors = ['#43e97b','#38f9d7','#6c63ff','#f9ca24','#ff6b6b','#a29bfe'];
            for (let i = 0; i < 60; i++) {
                const el = document.createElement('div');
                el.className = 'confetti-piece';
                el.style.left = Math.random() * 100 + 'vw';
                el.style.top = '-20px';
                el.style.background = colors[i % colors.length];
                el.style.animationDuration = (1.5 + Math.random() * 2) + 's';
                el.style.animationDelay = (Math.random() * 1) + 's';
                document.body.appendChild(el);
                setTimeout(() => el.remove(), 4000);
            }
        })();
        </script>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    if st.button("Back to Dashboard", type="primary", width="stretch", icon=":material/home:"):
        st.session_state.pop("qr_attendance_done", None)
        st.rerun()


# ---------------------------------------------------------------------------
# QR scan handler — called at the top of student_screen
# ---------------------------------------------------------------------------

def _handle_qr_scan():
    """
    Check for a pending QR token (stored by app.py in session state).
    If valid and student is logged in, record attendance and show done animation.
    Returns True if we consumed the token and should stop rendering the normal UI.
    """
    token = st.session_state.get("pending_qr_token")
    if not token:
        return False

    # Student must be logged in to record attendance
    if not st.session_state.get("is_logged_in") or st.session_state.get("user_role") != "student":
        # Keep token, will retry after login
        return False

    subject_id = validate_qr_token(token)
    # Consume the token regardless of outcome
    st.session_state.pop("pending_qr_token", None)

    if subject_id is None:
        st.error("❌ QR code has expired or is invalid. Please ask your teacher to refresh it.")
        time.sleep(2)
        st.rerun()
        return True

    student_id = st.session_state.student_data["student_id"]
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    log_single_attendance(student_id, subject_id, timestamp)
    st.session_state.qr_attendance_done = True
    st.rerun()
    return True


# ---------------------------------------------------------------------------
# Student dashboard (enrolled subjects)
# ---------------------------------------------------------------------------

def student_dashboard():
    # Show done animation if attendance was just recorded via QR
    if st.session_state.get("qr_attendance_done"):
        style_background_dashboard()
        style_base_layout()
        c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
        with c1:
            header_dashboard()
        with c2:
            st.subheader(f"Welcome, {st.session_state.student_data['name']}")
        _show_done_animation(0)
        footer_dashboard()
        return

    student_data = st.session_state.student_data
    student_id = student_data['student_id']
    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"""Welcome, {student_data['name']} """)
        if st.button("Logout", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['is_logged_in'] = False
            st.session_state['login_type'] = None
            if "student_data" in st.session_state:
                del st.session_state.student_data
            st.rerun()

    st.space()

    c1, c2 = st.columns(2)
    with c1:
        st.header('Your Enrolled Subjects')
    with c2:
        if st.button('Enroll in Subject', type='primary', width='stretch'):
            enroll_dialog()

    st.divider()

    with st.spinner('Loading your enrolled subjects..'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    stats_map = {}

    for log in logs:
        sid = log['subject_id']

        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0}

        stats_map[sid]['total'] += 1

        if log.get('is_present'):
            stats_map[sid]['attended'] += 1

    cols = st.columns(2)
    for i, sub_node in enumerate(subjects):
        sub = sub_node['subjects']
        sid = sub['subject_id']

        stats = stats_map.get(sid, {"total": 0, "attended": 0})

        with cols[i % 2]:
            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub['section'],
                stats=[
                    ('📅', 'Total', stats['total']),
                    ('✅', 'Attended', stats['attended']),
                ]
            )
    footer_dashboard()


# ---------------------------------------------------------------------------
# Student screen entry point
# ---------------------------------------------------------------------------

def student_screen():
    style_background_dashboard()
    style_base_layout()

    if "student_data" in st.session_state:
        # Try to process a pending QR token now that the student is logged in
        _handle_qr_scan()
        student_dashboard()
        return

    c1, c2 = st.columns(2, vertical_alignment='center', gap='xxlarge')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='loginbackbtn', shortcut="control+backspace"):
            st.session_state['login_type'] = None
            st.rerun()

    st.header('Login using FaceID', text_alignment='center')
    st.space()
    st.space()

    # Use session_state flag so registration form survives reruns
    if 'show_face_registration' not in st.session_state:
        st.session_state.show_face_registration = False

    photo_source = st.camera_input("Position your face in the center")

    if photo_source:
        # Always reset registration flag when a new photo is taken
        st.session_state.show_face_registration = False

        # Convert to RGB numpy array — dlib strictly requires uint8 RGB
        img = np.array(Image.open(photo_source).convert('RGB'))

        with st.spinner('AI is scanning..'):
            detected, all_ids, num_faces = predict_attendance(img)

            if num_faces == 0:
                st.warning('No face detected! Make sure your face is clearly visible and well-lit.')
            elif num_faces > 1:
                st.warning('Multiple faces detected! Please ensure only one person is in the frame.')
            else:
                if detected:
                    student_id = list(detected.keys())[0]
                    student = get_student_by_id(student_id)

                    if student:
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = 'student'
                        st.session_state.student_data = student
                        st.session_state.show_face_registration = False
                        st.toast(f"Welcome Back {student['name']}")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info('Face not recognized! You might be a new student!')
                    st.session_state.show_face_registration = True

    if st.session_state.show_face_registration and photo_source:
        with st.container(border=True):
            st.header('Register new Profile')
            new_name = st.text_input("Enter your name", placeholder='E.g. Hamza Rizvi')

            if st.button('Create Account', type='primary'):
                if new_name:
                    with st.spinner('Creating profile..'):
                        img = np.array(Image.open(photo_source).convert('RGB'))
                        encodings = get_face_embeddings(img)
                        if encodings:
                            face_emb = encodings[0].tolist()

                            response_data = create_student(new_name, face_embedding=face_emb, voice_embedding=None)

                            if response_data:
                                train_classifier()
                                st.session_state.is_logged_in = True
                                st.session_state.user_role = 'student'
                                st.session_state.student_data = response_data[0]
                                st.session_state.show_face_registration = False
                                st.toast(f'Profile Created! Hi {new_name}!')
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error("Couldn't capture your facial features. Please retake the photo in better lighting.")

                else:
                    st.warning('Please enter your name!')

    footer_dashboard()