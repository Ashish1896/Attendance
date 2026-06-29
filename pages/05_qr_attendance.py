"""
pages/05_qr_attendance.py — No login required.
"""

import streamlit as st
import pandas as pd
from datetime import date

from utils.ui_helpers         import setup_page, render_sidebar_brand, page_title, section_header, empty_state, inject_css
from services.attendance_service import get_all_students, mark_attendance, get_today_attendance
from services.qr_service      import generate_and_save_qr, get_student_qr, validate_qr_token
from database.supabase_client import get_db

setup_page("QR Attendance", "📱")
inject_css()
render_sidebar_brand()

page_title("QR Code Attendance", "Scan or enter QR token for instant attendance", "📱")
st.markdown("---")

tab_scan, tab_qr_view = st.tabs(["📷 Mark Attendance (QR)", "🖨️ View / Generate QR Codes"])

with tab_scan:
    st.info("📱 Enter the QR token below, or select a student manually to mark attendance.")
    col_form, col_result = st.columns(2)

    with col_form:
        section_header("Enter QR Token")
        with st.form("qr_attendance_form"):
            qr_token_raw = st.text_area("QR Code Content",
                placeholder="ATTENDANCE_QR|<student_id>|<token>", height=100, key="qr_token_input")
            students = get_all_students()
            student_map = {s["id"]: f"{s['name']} ({s['roll_number']})" for s in students}
            manual_id = st.selectbox("Or select student manually",
                options=[""] + list(student_map.keys()),
                format_func=lambda sid: student_map.get(sid, "— Select —") if sid else "— Select —",
                key="qr_manual_student")
            status_opt = st.selectbox("Status", ["present", "late"], key="qr_status")
            submit = st.form_submit_button("✅ Mark Attendance", use_container_width=True)

    with col_result:
        section_header("Result")
        if submit:
            resolved = None
            if qr_token_raw and qr_token_raw.strip():
                resolved = validate_qr_token(qr_token_raw.strip())
                if not resolved:
                    st.error("❌ Invalid or expired QR code.")
            elif manual_id:
                try:
                    res = get_db().table("students").select("*").eq("id", manual_id).single().execute()
                    resolved = res.data
                except Exception:
                    pass

            if resolved:
                name, roll, dept, s_id = (resolved.get("name",""), resolved.get("roll_number",""),
                                           resolved.get("department",""), resolved.get("id",""))
                st.success(f"✅ **Verified: {name}**")
                st.markdown(f"| | |\n|---|---|\n| 👤 | **{name}** |\n| 🆔 | {roll} |\n| 🏫 | {dept} |")
                ok, msg = mark_attendance(student_id=s_id,
                    method="qr" if (qr_token_raw and qr_token_raw.strip()) else "manual",
                    status=status_opt)
                if ok: st.success(f"🎉 {msg}"); st.balloons()
                else:  st.warning(f"⚠️ {msg}")
            elif submit:
                empty_state("📱", "No Student Selected", "Enter QR content or select a student.")

    st.markdown("---")
    section_header("Today's QR Attendance")
    records = [r for r in get_today_attendance() if r.get("method") in ("qr","manual")]
    if records:
        df = pd.DataFrame(records)
        cols = [c for c in ["student_name","roll_number","department","time","method","status"] if c in df.columns]
        show = df[cols].rename(columns={"student_name":"Student","roll_number":"Roll No",
                                         "department":"Dept","time":"Time","method":"Method","status":"Status"})
        if "Method" in show.columns:
            show["Method"] = show["Method"].map({"qr":"📱 QR","manual":"✍️ Manual"}).fillna(show["Method"])
        st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        empty_state("📱", "No QR Attendance Today", "Records appear after QR scanning.")

with tab_qr_view:
    section_header("Student QR Codes")
    students = get_all_students()
    if not students:
        empty_state("📱", "No Students", "Add students first.")
        st.stop()

    col_bulk, col_sel = st.columns([1, 2])
    with col_bulk:
        if st.button("🔄 Regenerate All QR Codes", use_container_width=True, key="regen_all"):
            prog = st.progress(0)
            for i, s in enumerate(students):
                generate_and_save_qr(s["id"])
                prog.progress((i+1)/len(students))
            st.success(f"✅ Regenerated {len(students)} QR codes!")
            st.rerun()
    with col_sel:
        sel_id = st.selectbox("View student QR", options=[s["id"] for s in students],
                               format_func=lambda sid: next((f"{s['name']} ({s['roll_number']})" for s in students if s["id"]==sid), sid),
                               key="qr_view_student")

    if sel_id:
        sel = next((s for s in students if s["id"]==sel_id), None)
        if sel:
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                qr_data = get_student_qr(sel_id)
                if qr_data:
                    st.markdown(f'<div style="background:white;padding:1.5rem;border-radius:16px;display:inline-block;"><img src="{qr_data}" style="width:200px;height:200px;"/></div>', unsafe_allow_html=True)
                    st.caption("Scan with any QR reader")
                else:
                    st.warning("No QR yet.")
                    if st.button("📱 Generate Now", key="gen_single"):
                        ok, msg = generate_and_save_qr(sel_id)
                        st.success(msg) if ok else st.error(msg)
                        if ok: st.rerun()
            with c2:
                st.markdown(f"### {sel['name']}\n| | |\n|---|---|\n| 🆔 Roll | {sel['roll_number']} |\n| 🏫 Dept | {sel['department']} |\n| 📧 Email | {sel['email']} |")
                if st.button("🔄 Regen QR", key="regen_single", use_container_width=True):
                    ok, msg = generate_and_save_qr(sel_id)
                    st.success(msg) if ok else st.error(msg)
                    if ok: st.rerun()
