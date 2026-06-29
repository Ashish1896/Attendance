import streamlit as st


def _render_footer(text_color: str = "black") -> None:
    """Shared footer HTML renderer; only the text color differs per context."""
    logo_url = "https://i.ibb.co/4r5X1FY/apnacollege.png"
    st.markdown(f"""
        <div style="margin-top:2rem; display:flex; gap:6px; justify-content:center; align-items:center">
        <p style="font-weight:bold; color:{text_color};"> Created with ❤️ by </p>  
        <img src='{logo_url}' style='max-height:25px' />
        </div>
            """, unsafe_allow_html=True)


def footer_home() -> None:
    _render_footer(text_color="white")


def footer_dashboard() -> None:
    _render_footer(text_color="black")