"""
QR Attendance Dialog — Teacher side
-------------------------------------
Displays a rotating QR code that refreshes every 20 seconds.
The QR encodes a signed token in the app URL so students can scan
and have their attendance recorded automatically.
"""

import time
import streamlit as st
from src.pipelines.qr_pipeline import generate_qr_token, make_qr_image, TOKEN_TTL_SECONDS


@st.fragment(run_every=1)
def _qr_live_display(selected_subject_id: int):
    """Fragment that auto-reruns every second to update the countdown live."""
    # Initialise token on first render
    if "qr_gen_start" not in st.session_state:
        st.session_state.qr_gen_start = time.time()
        st.session_state.qr_token = generate_qr_token(selected_subject_id)

    elapsed = time.time() - st.session_state.qr_gen_start
    remaining = TOKEN_TTL_SECONDS - elapsed

    # Rotate token when expired
    if remaining <= 0:
        st.session_state.qr_gen_start = time.time()
        st.session_state.qr_token = generate_qr_token(selected_subject_id)
        remaining = TOKEN_TTL_SECONDS

    token = st.session_state.qr_token

    # Build scan URL
    base_url = st.get_option("browser.serverAddress") or "localhost"
    port = st.get_option("browser.serverPort") or 8501
    scan_url = f"http://{base_url}:{port}/?qr-token={token}&subject={selected_subject_id}"

    # Render QR image
    qr_img = make_qr_image(scan_url, scale=10)
    st.image(qr_img, width="stretch")

    # Progress bar + countdown
    st.progress(max(0.0, remaining / TOKEN_TTL_SECONDS))

    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown(
            f"""
            <p style="text-align:center;font-size:2rem;font-weight:800;color:#6c63ff;margin:0">
                🔄 {int(remaining)}s
            </p>
            <p style="text-align:center;font-size:0.8rem;color:#888;margin:0">
                QR refreshes automatically
            </p>
            """,
            unsafe_allow_html=True,
        )


@st.dialog("📱 QR Attendance")
def qr_attendance_dialog(selected_subject_id: int):
    st.markdown(
        '<p style="text-align:center;font-size:1rem;color:#555;margin-bottom:0.5rem">'
        "Students — scan this QR code to mark attendance"
        "</p>",
        unsafe_allow_html=True,
    )

    _qr_live_display(selected_subject_id)

    st.divider()
    st.caption(
        f"Subject ID: `{selected_subject_id}` · Token expires every {TOKEN_TTL_SECONDS} seconds"
    )
