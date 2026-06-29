"""
pages/07_reports.py — No login required.
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from utils.ui_helpers         import setup_page, render_sidebar_brand, page_title, section_header, empty_state, inject_css
from utils.constants          import DEPARTMENTS
from utils.exporters          import df_to_csv, df_to_excel, make_filename
from services.attendance_service import get_attendance_range, get_all_students, get_student_summary

setup_page("Reports", "📄")
inject_css()
render_sidebar_brand()

page_title("Reports", "Generate and download attendance reports", "📄")
st.markdown("---")

tab_att, tab_stu = st.tabs(["📅 Attendance Report", "👨‍🎓 Student Report"])

with tab_att:
    st.markdown("### 🎛️ Filters")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        rtype = st.selectbox("Report Type", ["Custom Range","Daily","Weekly","Monthly"], key="rpt_type")
    today = date.today()
    if rtype == "Daily":   start_date = end_date = today
    elif rtype == "Weekly":  start_date = today - timedelta(days=today.weekday()); end_date = today
    elif rtype == "Monthly": start_date = today.replace(day=1); end_date = today
    else:
        with col2: start_date = st.date_input("From", value=today - timedelta(days=30), key="rpt_start")
        with col3: end_date   = st.date_input("To",   value=today, key="rpt_end")
    with col4:
        dept_filter = st.selectbox("Department", ["All"] + DEPARTMENTS, key="rpt_dept")

    students = get_all_students()
    stu_opts = {"": "All Students"}
    stu_opts.update({s["id"]: f"{s['name']} ({s['roll_number']})" for s in students})
    stu_filter = st.selectbox("Student", list(stu_opts.keys()), format_func=lambda k: stu_opts[k], key="rpt_student")
    st.markdown("---")

    if st.button("🔍 Generate Report", use_container_width=True, type="primary"):
        with st.spinner("Fetching data…"):
            records = get_attendance_range(start_date=start_date, end_date=end_date,
                student_id=stu_filter or None, department=dept_filter if dept_filter != "All" else None)

        if not records:
            st.warning("No records found for the selected filters.")
        else:
            df = pd.DataFrame(records)
            col_map = {"date":"Date","time":"Time","student_name":"Student Name","roll_number":"Roll Number",
                       "department":"Department","student_email":"Email","method":"Method","status":"Status"}
            show_cols = [c for c in col_map if c in df.columns]
            show = df[show_cols].rename(columns=col_map).copy()
            if "Method" in show.columns:
                show["Method"] = show["Method"].map({"face":"📷 Face","qr":"📱 QR","manual":"✍️ Manual"}).fillna(show["Method"])
            if "Status" in show.columns:
                show["Status"] = show["Status"].map({"present":"✅ Present","absent":"❌ Absent","late":"⏰ Late"}).fillna(show["Status"])

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Records", len(df))
            m2.metric("Present", len(df[df.get("status","") == "present"]) if "status" in df.columns else "—")
            m3.metric("Unique Students", df["student_name"].nunique() if "student_name" in df.columns else "—")
            m4.metric("Range", f"{start_date} → {end_date}")

            srch = st.text_input("🔍 Search results…", key="rpt_search")
            if srch:
                mask = show.astype(str).apply(lambda c: c.str.contains(srch, case=False, na=False)).any(axis=1)
                show = show[mask]

            st.dataframe(show, use_container_width=True, hide_index=True, height=420)
            st.caption(f"{len(show)} records")
            st.markdown("---")
            section_header("Download")
            export = df[show_cols].rename(columns=col_map)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📥 Download CSV",  df_to_csv(export),
                    make_filename("attendance_report","csv"), "text/csv", use_container_width=True)
            with c2:
                st.download_button("📊 Download Excel", df_to_excel(export,"Attendance"),
                    make_filename("attendance_report","xlsx"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

with tab_stu:
    st.markdown("### 👨‍🎓 Student-wise Attendance Summary")
    if st.button("🔍 Load Student Report", use_container_width=True, key="load_stu"):
        with st.spinner("Generating…"):
            summary = get_student_summary()
        if not summary:
            empty_state("👨‍🎓", "No Students", "Add students and record attendance first.")
        else:
            df_s = pd.DataFrame(summary)
            if "attendance_pct" in df_s.columns:
                df_s = df_s.sort_values("attendance_pct", ascending=False)
            col_map_s = {"name":"Student Name","roll_number":"Roll Number","department":"Department",
                         "email":"Email","total_present":"Days Present","attendance_pct":"Attendance %"}
            show_cols_s = [c for c in col_map_s if c in df_s.columns]
            show_s = df_s[show_cols_s].rename(columns=col_map_s).copy()
            if "Attendance %" in show_s.columns:
                show_s["Attendance %"] = show_s["Attendance %"].apply(lambda x: f"{float(x or 0):.1f}%")

            dept_s = st.selectbox("Filter by Department", ["All"] + DEPARTMENTS, key="stu_rpt_dept")
            if dept_s != "All" and "Department" in show_s.columns:
                show_s = show_s[show_s["Department"] == dept_s]

            st.dataframe(show_s, use_container_width=True, hide_index=True, height=400)
            st.caption(f"{len(show_s)} students")
            st.markdown("---")
            export_s = df_s[show_cols_s].rename(columns=col_map_s)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📥 Download CSV",  df_to_csv(export_s),
                    make_filename("student_report","csv"), "text/csv", use_container_width=True)
            with c2:
                st.download_button("📊 Download Excel", df_to_excel(export_s,"Student Summary"),
                    make_filename("student_report","xlsx"),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
