"""
pages/02_students.py
====================
Student Management — Add, Edit, Delete. No login required.
"""

import streamlit as st
import pandas as pd

from utils.ui_helpers         import setup_page, render_sidebar_brand, page_title, section_header, empty_state, inject_css
from utils.constants          import DEPARTMENTS
from utils.validators         import validate_email, validate_roll_number, validate_name, validate_phone, ValidationError
from services.attendance_service import get_all_students, create_student, update_student, delete_student, get_student_by_id
from services.qr_service      import generate_and_save_qr


setup_page("Students", "👨‍🎓")
inject_css()
render_sidebar_brand()

page_title("Student Management", "Add, edit, and manage student records", "👨‍🎓")
st.markdown("---")

tab_list, tab_add = st.tabs(["📋 All Students", "➕ Add Student"])

# ══════════════════════════════════════════════════════════════
# TAB 1: Student List
# ══════════════════════════════════════════════════════════════
with tab_list:
    students = get_all_students()

    col_search, col_dept, col_refresh = st.columns([3, 2, 1])
    with col_search:
        search_q = st.text_input("🔍 Search", placeholder="Name, roll, or email…", key="student_search")
    with col_dept:
        dept_filter = st.selectbox("🏫 Department", ["All"] + DEPARTMENTS, key="student_dept_filter")
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    if students:
        df = pd.DataFrame(students)
        if search_q:
            mask = (df["name"].str.contains(search_q, case=False, na=False) |
                    df["roll_number"].str.contains(search_q, case=False, na=False) |
                    df["email"].str.contains(search_q, case=False, na=False))
            df = df[mask]
        if dept_filter != "All":
            df = df[df["department"] == dept_filter]

        st.caption(f"Showing {len(df)} of {len(students)} students")

        display_df = df[["name","roll_number","department","email","phone","face_images"]].copy()
        display_df["face_images"] = display_df["face_images"].apply(
            lambda x: f"✅ {x} images" if x and int(x) >= 3 else (f"⚠️ {x}" if x else "❌ None"))
        display_df.columns = ["Name","Roll No","Department","Email","Phone","Face Status"]
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=380)

        st.markdown("---")
        section_header("Edit / Delete Student")

        if len(df) > 0:
            all_ids   = df["id"].tolist()
            id_name_map = {s["id"]: f"{s['name']} — {s['roll_number']}" for s in students if s["id"] in all_ids}

            selected_id = st.selectbox("Select student", options=all_ids,
                                        format_func=lambda sid: id_name_map.get(sid, sid),
                                        key="edit_student_select")
            student_data = get_student_by_id(selected_id) if selected_id else None

            if student_data:
                col_edit, col_del, col_qr = st.columns([2, 1, 1])

                with col_edit:
                    with st.expander("✏️ Edit Student", expanded=False):
                        with st.form(f"edit_form_{selected_id}"):
                            e_name  = st.text_input("Name",        value=student_data.get("name",""))
                            e_email = st.text_input("Email",       value=student_data.get("email",""))
                            e_roll  = st.text_input("Roll Number", value=student_data.get("roll_number",""))
                            dept_idx = DEPARTMENTS.index(student_data.get("department", DEPARTMENTS[0])) if student_data.get("department") in DEPARTMENTS else 0
                            e_dept  = st.selectbox("Department", DEPARTMENTS, index=dept_idx)
                            e_phone = st.text_input("Phone",       value=student_data.get("phone","") or "")
                            save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)

                        if save_btn:
                            try:
                                ok, msg = update_student(selected_id, {
                                    "name":        validate_name(e_name),
                                    "email":       validate_email(e_email),
                                    "roll_number": validate_roll_number(e_roll),
                                    "department":  e_dept,
                                    "phone":       validate_phone(e_phone),
                                })
                                st.success(msg) if ok else st.error(msg)
                                if ok: st.rerun()
                            except ValidationError as exc:
                                st.error(str(exc))

                with col_del:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Delete", key=f"del_{selected_id}", use_container_width=True):
                        st.session_state["confirm_delete"] = selected_id
                    if st.session_state.get("confirm_delete") == selected_id:
                        st.warning(f"Delete **{student_data.get('name')}**?")
                        if st.button("⚠️ Confirm", key="confirm_del_btn"):
                            ok, msg = delete_student(selected_id)
                            st.session_state.pop("confirm_delete", None)
                            st.success(msg) if ok else st.error(msg)
                            if ok: st.rerun()

                with col_qr:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("📱 Gen QR", key=f"qr_{selected_id}", use_container_width=True):
                        ok, msg = generate_and_save_qr(selected_id)
                        st.success(msg) if ok else st.error(msg)
                        if ok: st.rerun()
    else:
        empty_state("👨‍🎓", "No Students Found", "Add your first student using the 'Add Student' tab.")

# ══════════════════════════════════════════════════════════════
# TAB 2: Add Student
# ══════════════════════════════════════════════════════════════
with tab_add:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("add_student_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            a_name  = st.text_input("👤 Full Name *",   placeholder="e.g. Aarav Sharma")
            a_roll  = st.text_input("🆔 Roll Number *", placeholder="e.g. CS2024001")
            a_dept  = st.selectbox("🏫 Department *",   DEPARTMENTS)
        with col2:
            a_email = st.text_input("📧 Email *",       placeholder="student@school.edu")
            a_phone = st.text_input("📞 Phone",         placeholder="+91-9876543210")

        gen_qr  = st.checkbox("📱 Auto-generate QR code", value=True)
        st.markdown("<br>", unsafe_allow_html=True)
        add_btn = st.form_submit_button("➕ Add Student", use_container_width=True)

    if add_btn:
        if not all([a_name, a_roll, a_email, a_dept]):
            st.error("Name, Roll Number, Email, and Department are required.")
        else:
            try:
                ok, msg, new_id = create_student({
                    "name":        validate_name(a_name),
                    "email":       validate_email(a_email),
                    "roll_number": validate_roll_number(a_roll),
                    "department":  a_dept,
                    "phone":       validate_phone(a_phone),
                })
                if ok and new_id:
                    if gen_qr:
                        qr_ok, qr_msg = generate_and_save_qr(new_id)
                    st.success(f"✅ {msg}" + (" QR generated!" if gen_qr and qr_ok else ""))
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            except ValidationError as exc:
                st.error(f"❌ {exc}")
