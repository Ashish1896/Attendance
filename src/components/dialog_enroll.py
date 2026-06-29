import streamlit as st
from src.database.db import enroll_student_to_subject, get_subject_by_code, check_enrollment
import time


@st.dialog("Enroll in Subject")
def enroll_dialog():
    st.write('Enter the subject code provided by your teacher to enroll')
    with st.form("enroll_form"):
        join_code = st.text_input('Subject Code', placeholder='Eg. CS101')
        submitted = st.form_submit_button('Enroll now', type='primary', use_container_width=True)

        if submitted:
            if join_code:
                subject = get_subject_by_code(join_code.strip())
                if subject:
                    student_id = st.session_state.student_data['student_id']

                    if check_enrollment(student_id, subject['subject_id']):
                        st.warning('You are already enrolled in this program')
                    else:
                        enroll_student_to_subject(student_id, subject['subject_id'])
                        st.success('Successfully enrolled!')
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error('Subject not found. Check the code and try again.')
            else:
                st.warning('Please enter a subject code')