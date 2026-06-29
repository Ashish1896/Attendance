"""
pages/01_dashboard.py
=====================
Admin Dashboard — KPI metrics, trend chart, recent activity.
No login required.
"""

import streamlit as st
import pandas as pd
from datetime import date

from utils.ui_helpers     import setup_page, render_sidebar_brand, page_title, section_header, empty_state, inject_css
from services.attendance_service import get_today_stats, get_today_attendance
from services.analytics_service  import get_daily_attendance, build_daily_chart, get_department_stats, build_department_pie


setup_page("Dashboard", "📊")
inject_css()
render_sidebar_brand()

page_title("Dashboard", "Real-time overview of today's attendance", "📊")
st.markdown("---")

# ── KPI Metrics ──────────────────────────────────────────────
stats = get_today_stats()
total   = stats.get("total_students",  0)
present = stats.get("present_count",   0)
absent  = stats.get("absent_count",    0)
pct     = float(stats.get("attendance_pct", 0.0))

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("👨‍🎓 Total Students",  total)
with col2: st.metric("✅ Present Today",     present, delta=f"{pct:.1f}% attendance" if total > 0 else None)
with col3: st.metric("❌ Absent Today",      absent)
with col4: st.metric("📈 Attendance %",      f"{pct:.1f}%")

st.markdown("---")

# ── Charts Row ───────────────────────────────────────────────
col_left, col_right = st.columns([2, 1])

with col_left:
    section_header("Attendance Trend", "30 Days")
    daily_df = get_daily_attendance(30)
    st.plotly_chart(build_daily_chart(daily_df), use_container_width=True)

with col_right:
    section_header("By Department", "Today")
    dept_df = get_department_stats()
    st.plotly_chart(build_department_pie(dept_df), use_container_width=True)

st.markdown("---")

# ── Today's Attendance Table ─────────────────────────────────
section_header("Today's Attendance", date.today().strftime("%d %b %Y"))

today_records = get_today_attendance()
if today_records:
    df = pd.DataFrame(today_records)
    col_map = {"student_name":"Student","roll_number":"Roll No","department":"Department",
                "time":"Time","method":"Method","status":"Status"}
    cols = [c for c in col_map if c in df.columns]
    display_df = df[cols].rename(columns=col_map)
    if "Method" in display_df.columns:
        display_df["Method"] = display_df["Method"].map({"face":"📷 Face","qr":"📱 QR","manual":"✍️ Manual"}).fillna(display_df["Method"])
    if "Status" in display_df.columns:
        display_df["Status"] = display_df["Status"].map({"present":"✅ Present","absent":"❌ Absent","late":"⏰ Late"}).fillna(display_df["Status"])

    search = st.text_input("🔍 Search student…", placeholder="Name or Roll Number", key="dash_search")
    if search:
        mask = display_df.apply(lambda col: col.astype(str).str.contains(search, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]

    st.dataframe(display_df, use_container_width=True, hide_index=True,
                 height=min(400, 40 + len(display_df) * 35))
    st.caption(f"Showing {len(display_df)} of {len(today_records)} records")
else:
    empty_state("📋", "No Attendance Today", "Attendance will appear here as students check in.")

st.markdown("---")

# ── Department Breakdown ─────────────────────────────────────
section_header("Department Breakdown", "Today")
if dept_df is not None and not dept_df.empty:
    dept_display = dept_df.copy()
    dept_display["Attendance %"] = dept_display["pct"].apply(lambda x: f"{x:.1f}%")
    dept_display = dept_display.rename(columns={"department":"Department","total":"Total","present":"Present"})[["Department","Total","Present","Attendance %"]]
    st.dataframe(dept_display, use_container_width=True, hide_index=True)
else:
    empty_state("🏫", "No department data", "Add students to see department stats.")
