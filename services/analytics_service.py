"""
services/analytics_service.py
==============================
Data aggregation for charts and analytics dashboards.
"""

import logging
from datetime import date, timedelta
from typing import List, Dict

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from database.supabase_client import get_db
from utils.constants import PLOTLY_TEMPLATE, PLOTLY_COLORS, DEPARTMENTS

logger = logging.getLogger(__name__)

TRANSPARENT_BG = dict(
    plot_bgcolor  = "rgba(0,0,0,0)",
    paper_bgcolor = "rgba(0,0,0,0)",
)


# ──────────────────────────────────────────────────────────────
# Data Fetching
# ──────────────────────────────────────────────────────────────
def get_daily_attendance(days: int = 30) -> pd.DataFrame:
    """Returns a DataFrame of daily attendance counts for the past N days."""
    start = date.today() - timedelta(days=days)
    try:
        db  = get_db()
        res = db.table("attendance").select("date, status").gte(
            "date", start.isoformat()
        ).execute()
        if not res.data:
            return pd.DataFrame(columns=["date", "present", "absent"])

        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"])

        # Total students for absent calculation
        total_res = db.table("students").select("id", count="exact").eq("is_active", True).execute()
        total = total_res.count or 0

        pivot = df[df["status"] == "present"].groupby("date").size().reset_index(name="present")
        # Fill missing dates
        date_range = pd.date_range(start=start, end=date.today())
        pivot = pivot.set_index("date").reindex(date_range, fill_value=0).reset_index()
        pivot.columns = ["date", "present"]
        pivot["absent"] = total - pivot["present"]
        pivot["absent"] = pivot["absent"].clip(lower=0)
        return pivot
    except Exception as exc:
        logger.error(f"get_daily_attendance: {exc}")
        return pd.DataFrame(columns=["date", "present", "absent"])


def get_department_stats() -> pd.DataFrame:
    """Returns attendance percentage grouped by department."""
    try:
        db  = get_db()
        students_res = db.table("students").select("id, department").eq("is_active", True).execute()
        attend_res   = db.table("attendance").select("student_id, status").eq(
            "date", date.today().isoformat()
        ).execute()

        if not students_res.data:
            return pd.DataFrame()

        students_df = pd.DataFrame(students_res.data)
        attend_df   = pd.DataFrame(attend_res.data) if attend_res.data else pd.DataFrame(
            columns=["student_id", "status"]
        )

        if not attend_df.empty:
            present_ids = set(attend_df[attend_df["status"] == "present"]["student_id"])
            students_df["present"] = students_df["id"].isin(present_ids).astype(int)
        else:
            students_df["present"] = 0

        dept_stats = students_df.groupby("department").agg(
            total=("id", "count"),
            present=("present", "sum")
        ).reset_index()
        dept_stats["pct"] = (dept_stats["present"] / dept_stats["total"] * 100).round(1)
        return dept_stats
    except Exception as exc:
        logger.error(f"get_department_stats: {exc}")
        return pd.DataFrame()


def get_weekly_trend() -> pd.DataFrame:
    """Returns weekly attendance aggregated by week for the past 12 weeks."""
    try:
        start = date.today() - timedelta(weeks=12)
        db  = get_db()
        res = db.table("attendance").select("date, status").gte(
            "date", start.isoformat()
        ).eq("status", "present").execute()

        if not res.data:
            return pd.DataFrame()

        df = pd.DataFrame(res.data)
        df["date"] = pd.to_datetime(df["date"])
        df["week"] = df["date"].dt.to_period("W").astype(str)
        weekly = df.groupby("week").size().reset_index(name="present_count")
        return weekly
    except Exception as exc:
        logger.error(f"get_weekly_trend: {exc}")
        return pd.DataFrame()


def get_monthly_trend() -> pd.DataFrame:
    """Returns monthly attendance totals for the past 6 months."""
    try:
        start = date.today() - timedelta(days=180)
        db  = get_db()
        res = db.table("attendance").select("date, status").gte(
            "date", start.isoformat()
        ).eq("status", "present").execute()

        if not res.data:
            return pd.DataFrame()

        df = pd.DataFrame(res.data)
        df["date"]  = pd.to_datetime(df["date"])
        df["month"] = df["date"].dt.to_period("M").astype(str)
        monthly = df.groupby("month").size().reset_index(name="present_count")
        return monthly
    except Exception as exc:
        logger.error(f"get_monthly_trend: {exc}")
        return pd.DataFrame()


def get_method_distribution() -> Dict[str, int]:
    """Returns count of attendance records by method."""
    try:
        db  = get_db()
        for method in ["face", "qr", "manual"]:
            pass  # placeholder

        res = db.table("attendance").select("method").execute()
        if not res.data:
            return {}
        df = pd.DataFrame(res.data)
        return df["method"].value_counts().to_dict()
    except Exception as exc:
        logger.error(f"get_method_distribution: {exc}")
        return {}


# ──────────────────────────────────────────────────────────────
# Chart Builders
# ──────────────────────────────────────────────────────────────
def build_daily_chart(df: pd.DataFrame) -> go.Figure:
    """Builds a stacked bar chart of daily attendance."""
    if df.empty:
        return _empty_figure("No daily attendance data")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["date"], y=df["present"],
        name="Present", marker_color="#6C63FF",
        hovertemplate="<b>%{x}</b><br>Present: %{y}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        x=df["date"], y=df["absent"],
        name="Absent", marker_color="rgba(255,71,87,0.6)",
        hovertemplate="<b>%{x}</b><br>Absent: %{y}<extra></extra>"
    ))
    fig.update_layout(
        **TRANSPARENT_BG,
        template=PLOTLY_TEMPLATE,
        barmode="stack",
        title=dict(text="Daily Attendance", font=dict(color="#E8E8F0", size=16)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9999BB")),
        xaxis=dict(gridcolor="rgba(108,99,255,0.1)", color="#9999BB"),
        yaxis=dict(gridcolor="rgba(108,99,255,0.1)", color="#9999BB"),
        height=380,
        margin=dict(t=50, b=40, l=40, r=20),
    )
    return fig


def build_department_pie(df: pd.DataFrame) -> go.Figure:
    """Builds a donut chart of present students by department."""
    if df.empty:
        return _empty_figure("No department data")

    fig = go.Figure(go.Pie(
        labels=df["department"],
        values=df["present"],
        hole=0.55,
        marker=dict(colors=PLOTLY_COLORS),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Present: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **TRANSPARENT_BG,
        template=PLOTLY_TEMPLATE,
        title=dict(text="Department Attendance (Today)", font=dict(color="#E8E8F0", size=16)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9999BB")),
        height=380,
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig


def build_weekly_chart(df: pd.DataFrame) -> go.Figure:
    """Builds a line chart of weekly attendance."""
    if df.empty:
        return _empty_figure("No weekly data")

    fig = go.Figure(go.Scatter(
        x=df["week"],
        y=df["present_count"],
        mode="lines+markers",
        line=dict(color="#6C63FF", width=2.5),
        marker=dict(color="#00D4AA", size=8),
        fill="tozeroy",
        fillcolor="rgba(108,99,255,0.1)",
        hovertemplate="<b>%{x}</b><br>Present: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **TRANSPARENT_BG,
        template=PLOTLY_TEMPLATE,
        title=dict(text="Weekly Attendance Trend", font=dict(color="#E8E8F0", size=16)),
        xaxis=dict(gridcolor="rgba(108,99,255,0.1)", color="#9999BB", tickangle=-30),
        yaxis=dict(gridcolor="rgba(108,99,255,0.1)", color="#9999BB"),
        height=380,
        margin=dict(t=50, b=60, l=40, r=20),
    )
    return fig


def build_monthly_chart(df: pd.DataFrame) -> go.Figure:
    """Builds a bar chart of monthly attendance."""
    if df.empty:
        return _empty_figure("No monthly data")

    fig = go.Figure(go.Bar(
        x=df["month"],
        y=df["present_count"],
        marker=dict(
            color=df["present_count"],
            colorscale=[[0, "#4D45CC"], [1, "#00D4AA"]],
            showscale=False,
        ),
        hovertemplate="<b>%{x}</b><br>Total Present: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **TRANSPARENT_BG,
        template=PLOTLY_TEMPLATE,
        title=dict(text="Monthly Attendance Summary", font=dict(color="#E8E8F0", size=16)),
        xaxis=dict(gridcolor="rgba(108,99,255,0.1)", color="#9999BB"),
        yaxis=dict(gridcolor="rgba(108,99,255,0.1)", color="#9999BB"),
        height=380,
        margin=dict(t=50, b=40, l=40, r=20),
    )
    return fig


def build_method_pie(method_dict: Dict[str, int]) -> go.Figure:
    if not method_dict:
        return _empty_figure("No method data")
    labels = list(method_dict.keys())
    values = list(method_dict.values())
    icons  = {"face": "📷 Face", "qr": "📱 QR", "manual": "✍️ Manual"}
    labels = [icons.get(l, l) for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.5,
        marker=dict(colors=["#6C63FF", "#00D4AA", "#FFB347"]),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
    ))
    fig.update_layout(
        **TRANSPARENT_BG,
        template=PLOTLY_TEMPLATE,
        title=dict(text="Attendance by Method", font=dict(color="#E8E8F0", size=16)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9999BB")),
        height=320,
        margin=dict(t=50, b=20, l=20, r=20),
    )
    return fig


def _empty_figure(message: str = "No data") -> go.Figure:
    """Returns a placeholder figure."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, showarrow=False,
        xref="paper", yref="paper", x=0.5, y=0.5,
        font=dict(color="#666688", size=16),
    )
    fig.update_layout(
        **TRANSPARENT_BG,
        template=PLOTLY_TEMPLATE,
        height=300,
    )
    return fig
