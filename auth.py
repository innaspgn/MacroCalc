import json
import os
import hashlib
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

USERS_FILE = "users.json"

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()

def _get_users_worksheet():
    try:
        if "gcp_service_account" not in st.secrets or "sheet_url" not in st.secrets:
            return None
        scopes = [
            "https://googleapis.com",
            "https://googleapis.com"
        ]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_url(st.secrets["sheet_url"])
        try:
            return sh.worksheet("users")
        except Exception:
            return sh.add_worksheet(title="users", rows=100, cols=5)
    except Exception:
        return None

def load_users() -> dict:
    ws = _get_users_worksheet()
    if ws is not None:
        try:
            raw = ws.acell("A1").value
            if raw:
                return json.loads(raw)
        except Exception:
            pass
        return {}

    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users: dict):
    ws = _get_users_worksheet()
    if ws is not None:
        ws.update("A1", [[json.dumps(users, ensure_ascii=False)]])
        return

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def render_auth_screen():
    st.subheader("Вход в личный кабинет")
    tab_login, tab_reg = st.tabs(["Войти", "Регистрация"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Логин или имя пользователя")
            password = st.text_input("Пароль", type="password")
            if st.form_submit_button("Войти", use_container_width=True):
                uname = username.strip().lower()
                users = load_users()
                if uname in users and users[uname]["password"] == _hash_password(password):
                    st.session_state.current_user = uname
                    st.session_state.display_name = users[uname].get("name", username.strip())
                    st.rerun()
                else:
                    st.error("Неверный логин или пароль")

    with tab_reg:
        with st.form("register_form"):
            new_name = st.text_input("Ваше имя")
            new_username = st.text_input("Придумайте логин (латиницей или цифрами)")
            new_password = st.text_input("Придумайте пароль", type="password")
            confirm_password = st.text_input("Повторите пароль", type="password")
            if st.form_submit_button("Создать аккаунт", use_container_width=True):
                uname = new_username.strip().lower()
                if not new_name.strip() or not uname or not new_password:
                    st.error("Заполните все поля")
                elif new_password != confirm_password:
                    st.error("Пароли не совпадают")
                elif len(new_password) < 4:
                    st.error("Пароль должен содержать минимум 4 символа")
                else:
                    users = load_users()
                    if uname in users:
                        st.error("Этот логин уже занят, выберите другой")
                    else:
                        users[uname] = {
                            "name": new_name.strip(),
                            "password": _hash_password(new_password)
                        }
                        save_users(users)
                        st.session_state.current_user = uname
                        st.session_state.display_name = new_name.strip()
                        st.success("Аккаунт создан")
                        st.rerun()
def update_user_credentials(username: str, new_display_name: str, new_password: str = "") -> tuple[bool, str]:
    users = load_users()
    if username not in users:
        return False, "Пользователь не найден"
    if new_display_name.strip():
        users[username]["name"] = new_display_name.strip()
        st.session_state.display_name = new_display_name.strip()
    if new_password:
        if len(new_password) < 4:
            return False, "Новый пароль должен содержать минимум 4 символа"
        users[username]["password"] = _hash_password(new_password)
    save_users(users)
    return True, "Данные аккаунта обновлены"
def delete_user_account(username: str):
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
