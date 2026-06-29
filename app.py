import streamlit as st

DOMAIN = "snapclass-main.streamlit.app"

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen

from src.components.dialog_auto_enroll import auto_enroll_dialog

def main():
    st.set_page_config(
        page_title='SnapClass - Making Attendance faster using AI',
        page_icon= "https://i.ibb.co/YTYGn5qV/logo.png"
    )
    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None

    match st.session_state['login_type']:
        case 'teacher':
            teacher_screen()

        case 'student':
            student_screen()
        
        case None:
            home_screen()


    # Store the join code in session state and clear the URL param immediately
    # to prevent the dialog from re-triggering on every subsequent rerun (REL-07)
    join_code = st.query_params.get('join-code')
    if join_code and 'pending_join_code' not in st.session_state:
        st.session_state.pending_join_code = join_code
        st.query_params.clear()

    if st.session_state.get('pending_join_code'):
        pending = st.session_state.pending_join_code
        if st.session_state.login_type != 'student':
            st.session_state.login_type = 'student'
            st.rerun()
        if st.session_state.get('is_logged_in') and st.session_state.get('user_role') == 'student':
            auto_enroll_dialog(pending)
            st.session_state.pop('pending_join_code', None)

    # Capture QR attendance token from URL — student scans QR → opens app → token recorded
    qr_token = st.query_params.get('qr-token')
    if qr_token and 'pending_qr_token' not in st.session_state:
        st.session_state.pending_qr_token = qr_token
        st.query_params.clear()
        # Ensure the app routes to the student screen
        if st.session_state.get('login_type') != 'student':
            st.session_state['login_type'] = 'student'
            st.rerun()

main()
