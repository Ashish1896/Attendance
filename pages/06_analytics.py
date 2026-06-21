"""
pages/06_analytics.py — No login required.
"""

import streamlit as st
import pandas as pd

from utils.ui_helpers         import setup_page, render_sidebar_brand, page_title, section_header, empty_state, inject_css
from services.analytics_service import (get_daily_attendance, get_weekly_trend, get_monthly_trend,
    get_department_stats, get_method_distribution, build_daily_chart, build_weekly_chart,
    build_monthly_chart, build_department_pie, build_method_pie)
from services.attendance_service import get_student_summary

setup_page("Analytics", "📈")
inject_css()
render_sidebar_brand()

page_title("Analytics", "Deep insights into attendance patterns and trends", "📈")
st.markdown("---")

col_days, _ = st.columns([1, 3])
with col_days:
    days_range = st.selectbox("📅 Date Range", [7, 14, 30, 60, 90], index=2,
                               format_func=lambda d: f"Last {d} days", key="analytics_range")

col1, col2 = st.columns([2, 1])
with col1:
    section_header("Daily Attendance", f"Last {days_range} days")
    st.plotly_chart(build_daily_chart(get_daily_attendance(days_range)), use_container_width=True)
with col2:
    section_header("By Department", "Today")
    st.plotly_chart(build_department_pie(get_department_stats()), use_container_width=True)

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    section_header("Weekly Trend", "Last 12 Weeks")
    st.plotly_chart(build_weekly_chart(get_weekly_trend()), use_container_width=True)
with col4:
    section_header("Monthly Summary", "Last 6 Months")
    st.plotly_chart(build_monthly_chart(get_monthly_trend()), use_container_width=True)

st.markdown("---")

col5, col6 = st.columns([1, 2])
with col5:
    section_header("Attendance Method")
    st.plotly_chart(build_method_pie(get_method_distribution()), use_container_width=True)
with col6:
    section_header("Department Statistics", "Today")
    dept_df = get_department_stats()
    if dept_df is not None and not dept_df.empty:
        for _, row in dept_df.iterrows():
            pct_val = float(row.get("pct", 0))
            color = "#4CAF50" if pct_val >= 75 else ("#FFB347" if pct_val >= 50 else "#FF4757")
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>"
                f"<span style='width:140px;font-size:0.82rem;color:#9999BB;'>{row['department'][:18]}</span>"
                f"<div style='flex:1;background:#1A1A2E;border-radius:4px;height:10px;'>"
                f"<div style='width:{min(pct_val,100):.0f}%;background:{color};height:10px;border-radius:4px;transition:width 0.5s;'></div>"
                f"</div><span style='width:45px;font-size:0.82rem;font-weight:700;color:{color};text-align:right;'>{pct_val:.0f}%</span>"
                f"</div>", unsafe_allow_html=True)
    else:
        empty_state("🏫", "No department data")

st.markdown("---")
section_header("Student Leaderboard", "All Time")
summary = get_student_summary()
if summary:
    df = pd.DataFrame(summary)
    if "attendance_pct" in df.columns:
        df = df.sort_values("attendance_pct", ascending=False).reset_index(drop=True)
    def rank(i):
        return ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
    cols_map = {"name":"Name","roll_number":"Roll No","department":"Department","total_present":"Days Present","attendance_pct":"Attendance %"}
    show_cols = [c for c in cols_map if c in df.columns]
    show = df[show_cols].rename(columns=cols_map)
    if "Attendance %" in show.columns:
        show["Attendance %"] = show["Attendance %"].apply(lambda x: f"{float(x or 0):.1f}%")
    show.insert(0, "Rank", [rank(i) for i in range(len(show))])
    st.dataframe(show, use_container_width=True, hide_index=True)
else:
    empty_state("🏆", "No Student Data", "Add students and mark attendance to see the leaderboard.")
