import streamlit as st
from auth import render_auth_screen
from storage import load_data
from screen_onboarding import show_calc_screen, show_measurements_screen, show_summary_screen
from screen_ration import show_ration_screen
from screen_profile import show_profile_screen
from screen_builder import show_builder_screen

st.set_page_config(page_title="Калькулятор КБЖУ", layout="centered")

st.markdown("""
<style>
    .stApp {
        background-color: #F7F3EE;
        color: #463532;
    }
    .block-container {
        max-width: 680px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3 {
        color: #4A313D !important;
        font-weight: 600 !important;
    }
    button[kind="primary"], div.stFormSubmitButton > button {
        background-color: #7D5A73 !important;
        color: #FAF6F2 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.65rem 1.2rem !important;
        font-weight: 500 !important;
        box-shadow: 0 2px 6px rgba(125, 90, 115, 0.18) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover, div.stFormSubmitButton > button:hover {
        background-color: #67475E !important;
        color: #FFFFFF !important;
    }
    button[kind="secondary"] {
        background-color: transparent !important;
        color: #8E6E78 !important;
        border: none !important;
        box-shadow: none !important;
        text-decoration: underline !important;
        text-underline-offset: 4px !important;
        padding: 0.4rem 0.6rem !important;
    }
    button[kind="secondary"]:hover {
        color: #5C3D49 !important;
        background-color: rgba(142, 110, 120, 0.08) !important;
        border-radius: 8px !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #EFE7DF !important;
        border: 1px solid #D5C3B3 !important;
        border-radius: 14px !important;
        padding: 10px 14px !important;
    }
    [data-testid="stMetric"] {
        background-color: transparent !important;
        border: none !important;
        padding: 4px 6px !important;
    }
    [data-testid="stMetricLabel"] {
        color: #7A5C61 !important;
    }
    [data-testid="stMetricValue"] {
        color: #4A313D !important;
        font-size: 1.45rem !important;
    }
    .stProgress > div > div > div > div {
        background-color: #9C6B84 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Калькулятор КБЖУ")

# Проверка авторизации
if "current_user" not in st.session_state or not st.session_state.current_user:
    render_auth_screen()
    st.stop()

data = load_data()

if "screen" not in st.session_state:
    st.session_state.screen = "ration" if data.get("onboarded") else "calc"

if "temp_targets" not in st.session_state:
    st.session_state.temp_targets = data["targets"].copy()

if "manual_mode" not in st.session_state:
    st.session_state.manual_mode = False

def go_to(screen_name: str):
    st.session_state.screen = screen_name
    st.rerun()

screens = {
    "calc": show_calc_screen,
    "measurements": show_measurements_screen,
    "summary": show_summary_screen,
    "ration": show_ration_screen,
    "profile": show_profile_screen,
    "builder": show_builder_screen
}

current_func = screens.get(st.session_state.screen, show_calc_screen)
current_func(data, go_to)

st.divider()
st.caption(f"Вы вошли как: {st.session_state.get('display_name', st.session_state.current_user)}")
if st.button("Выйти из аккаунта"):
    st.session_state.clear()
    st.rerun()
