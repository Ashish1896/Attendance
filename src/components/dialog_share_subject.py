import streamlit as st
import segno
import io


@st.cache_data
def _generate_qr_png(join_url: str) -> bytes:
    """Generate and cache a QR code PNG for the given URL.
    Cached so re-renders don't regenerate the same QR image (PERF-05).
    """
    qr = segno.make(join_url)
    out = io.BytesIO()
    qr.save(out, kind='png', scale=10, border=1)
    return out.getvalue()


@st.dialog("Share Class Link")
def share_subject_dialog(subject_name: str, subject_code: str) -> None:
    app_domain = "snapclass-main.streamlit.app"
    join_url = f"{app_domain}/?join-code={subject_code}"

    st.header("Scan to Join")

    qr_bytes = _generate_qr_png(join_url)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### Copy Link')
        st.code(join_url, language="text")
        st.code(subject_code, language="text")
        st.info('Copy this link to share on Whatsapp or Email')

    with col2:
        st.markdown('### Scan to Join')
        st.image(qr_bytes, caption='QR Code for class joining')