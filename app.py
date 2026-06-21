"""
app.py — Home / Landing Page
=============================
No login required. Opens directly to the dashboard overview.
"""

import streamlit as st
from utils.ui_helpers import setup_page, inject_css, render_sidebar_brand
from utils.constants  import APP_NAME, APP_ICON


setup_page("Home", APP_ICON)
inject_css()
render_sidebar_brand()

# ── Welcome hero ─────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:3rem 1rem 2rem;">
    <div style="font-size:4rem;margin-bottom:1rem;">🎓</div>
    <div style="font-size:2.4rem;font-weight:800;
                background:linear-gradient(135deg,#8B85FF,#00D4AA);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                background-clip:text;margin-bottom:0.5rem;">
        {APP_NAME}
    </div>
    <div style="color:#9999BB;font-size:1.05rem;margin-bottom:2.5rem;">
        AI-Powered · Face Recognition · QR Attendance · Real-time Analytics
    </div>
</div>
""", unsafe_allow_html=True)

# ── Quick-access cards ───────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

cards = [
    ("📊", "Dashboard",         "Live attendance stats & trends",   "pages/01_dashboard.py"),
    ("👨‍🎓","Students",          "Manage student records",           "pages/02_students.py"),
    ("📷", "Face Attendance",   "Webcam face recognition",          "pages/04_face_attendance.py"),
    ("📱", "QR Attendance",     "Scan QR code to mark attendance",  "pages/05_qr_attendance.py"),
]

for col, (icon, title, desc, page) in zip([c1, c2, c3, c4], cards):
    with col:
        st.markdown(f"""
        <div class="metric-card primary" style="text-align:center;padding:1.8rem 1rem;cursor:pointer;">
            <div style="font-size:2.2rem;margin-bottom:0.6rem;">{icon}</div>
            <div style="font-weight:700;font-size:1rem;margin-bottom:0.3rem;">{title}</div>
            <div style="font-size:0.78rem;color:#9999BB;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Open {title}", key=f"home_{title}", use_container_width=True):
            st.switch_page(page)

st.markdown("---")

# ── Feature highlights ───────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.markdown("""
    ### 🚀 Features
    - **📷 Face Recognition** — OpenCV Haar Cascade + 128-d embeddings
    - **📱 QR Code Backup** — Unique QR per student via segno
    - **📊 Live Dashboard** — KPI cards + Plotly trend charts
    - **📈 Analytics** — Daily / Weekly / Monthly charts
    - **📄 Reports** — Download CSV & Excel
    - **👨‍🎓 Student CRUD** — Add, edit, delete with department filter
    """)

with col_r:
    st.markdown("""
    ### ⚡ Tech Stack
    - **Frontend** — Streamlit (dark glassmorphism UI)
    - **Database** — Supabase PostgreSQL + pgvector
    - **Face Detection** — OpenCV Haar Cascade (lightweight)
    - **Embeddings** — 128-d block histogram (pure NumPy)
    - **QR Codes** — segno (high-quality color QR)
    - **Charts** — Plotly interactive charts
    """)

st.markdown("""
<div style="text-align:center;color:#444466;font-size:0.75rem;margin-top:2rem;">
    Smart Attendance System v1.0 · No login required · Open source
</div>
""", unsafe_allow_html=True)
