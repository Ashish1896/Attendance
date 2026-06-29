import streamlit as st


def header_home() -> None:
    logo_url = "https://i.ibb.co/YTYGn5qV/logo.png"
    st.markdown(
        f'<img src="{logo_url}" alt="Logo" style="width:50px">',
        unsafe_allow_html=True
    )


def header_dashboard() -> None:
    logo_url = "https://i.ibb.co/YTYGn5qV/logo.png"
    st.markdown(
        f'<img src="{logo_url}" alt="SnapClass Logo" style="width:50px">',
        unsafe_allow_html=True
    )