"""
utils/ui_helpers.py
===================
Reusable UI components and CSS injection for Streamlit.
"""

import base64
import streamlit as st
from pathlib import Path
from typing import Optional

from utils.constants import APP_NAME, APP_ICON


# ── CSS Injection ────────────────────────────────────────────
def inject_css() -> None:
    """Injects the global stylesheet into the Streamlit app."""
    css_path = Path(__file__).parent.parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        # Fallback inline dark styles
        st.markdown("""
        <style>
        [data-testid="stApp"] { background: #0E0E1A !important; color: #E8E8F0 !important; }
        [data-testid="stSidebar"] { background: #1A1A2E !important; }
        </style>
        """, unsafe_allow_html=True)


# ── Page Setup ───────────────────────────────────────────────
def setup_page(title: str, icon: str = APP_ICON, layout: str = "wide") -> None:
    """Configures page settings and injects CSS. Call once per page."""
    try:
        st.set_page_config(
            page_title=f"{title} | {APP_NAME}",
            page_icon=icon,
            layout=layout,
            initial_sidebar_state="expanded",
        )
    except st.errors.StreamlitAPIException:
        pass  # Already called
    inject_css()


# ── Sidebar Brand ────────────────────────────────────────────
def render_sidebar_brand() -> None:
    """Renders the app logo and brand name in the sidebar."""
    st.sidebar.markdown(f"""
    <div class="brand-header">
        <div class="brand-icon">🎓</div>
        <div>
            <div class="brand-name">{APP_NAME}</div>
            <div class="brand-tagline">AI-Powered Attendance</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Page Title ───────────────────────────────────────────────
def page_title(title: str, subtitle: str = "", icon: str = "") -> None:
    """Renders a styled page title."""
    prefix = f"{icon} " if icon else ""
    st.markdown(f"""
    <div>
        <div class="page-title">{prefix}{title}</div>
        {"<div class='page-subtitle'>" + subtitle + "</div>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


# ── Metric Cards ─────────────────────────────────────────────
def metric_card(
    label: str,
    value: str,
    delta: Optional[str] = None,
    color: str = "primary",
    icon: str = "📊",
) -> None:
    """Renders a glassmorphism metric card."""
    delta_html = (
        f'<div style="font-size:0.8rem;color:#4CAF50;margin-top:0.3rem;">▲ {delta}</div>'
        if delta else ""
    )
    st.markdown(f"""
    <div class="metric-card {color}">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ── Status Badge ─────────────────────────────────────────────
def status_badge(label: str, variant: str = "primary") -> str:
    """Returns HTML badge string. variant: success|danger|warning|primary|info"""
    return f'<span class="badge badge-{variant}">{label}</span>'


# ── Section Header ───────────────────────────────────────────
def section_header(title: str, badge: Optional[str] = None) -> None:
    badge_html = f'<span class="section-badge">{badge}</span>' if badge else ""
    st.markdown(f"""
    <div class="section-header">
        <span class="section-title">{title}</span>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


# ── Alert Helpers ─────────────────────────────────────────────
def success_toast(msg: str) -> None:
    st.toast(f"✅ {msg}", icon="✅")

def error_toast(msg: str) -> None:
    st.toast(f"❌ {msg}", icon="❌")

def info_toast(msg: str) -> None:
    st.toast(f"ℹ️ {msg}", icon="ℹ️")


# ── Empty State ──────────────────────────────────────────────
def empty_state(
    icon: str = "📭",
    title: str = "No data found",
    message: str = "",
) -> None:
    st.markdown(f"""
    <div style="text-align:center;padding:3rem;color:#666688;">
        <div style="font-size:3rem;margin-bottom:0.75rem;">{icon}</div>
        <div style="font-size:1.1rem;font-weight:600;color:#9999BB;margin-bottom:0.5rem;">{title}</div>
        <div style="font-size:0.85rem;">{message}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Auth Guards (no-op — login-free mode) ───────────────────
def require_login() -> dict:
    """No-op in login-free mode. Returns empty dict."""
    return {}


def require_admin() -> dict:
    """No-op in login-free mode. Returns empty dict."""
    return {}


# ── Image to Base64 ──────────────────────────────────────────
def img_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode()


# ── Logout (no-op in login-free mode) ───────────────────────
def render_logout() -> None:
    pass  # No login = no logout needed
