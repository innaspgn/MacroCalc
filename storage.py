import json
import os
import copy
from datetime import datetime
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

DEFAULT_DATA = {
    "onboarded": False,
    "targets_changed": False,
    "profile": {
        "gender": "Женский",
        "age": 30,
        "height": 175,
        "weight": 60.0,
        "activity": "Легкая активность (1–3 легкие тренировки в неделю или прогулки)",
        "goal": "Рекомпозиция",
        "hormones": "Нет особенностей",
        "takes_meds": False
    },
    "targets": {
        "kcal": 2000,
        "protein": 100,
        "fat": 60,
        "carbs": 250
    },
    "measurements": [],
    "dishes": [],
    "diary_by_date": {}
}

def _current_user() -> str:
    return st.session_state.get("current_user", "default")

def _get_gsheet():
    try:
        if "gcp_service_account" not in st.secrets or "sheet_url" not in st.secrets:
            return None
        base = "https://www." + "googleapis.com" + "/auth/"
        scopes = [base + "spreadsheets", base + "drive"]

        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url(st.secrets["sheet_url"])
    except Exception:
        return None

def load_data():
    user = _current_user()
    sh = _get_gsheet()
    if sh is not None:
        ws_name = f"data_{user}"[:30]
        try:
            ws = sh.worksheet(ws_name)
            raw = ws.acell("A1").value
            if raw:
                data = json.loads(raw)
                for k, v in DEFAULT_DATA.items():
                    if k not in data:
                        data[k] = copy.deepcopy(v)
                return data
        except Exception:
            pass
        fresh = copy.deepcopy(DEFAULT_DATA)
        save_data(fresh)
        return fresh

    file_path = f"user_data_{user}.json"
    if not os.path.exists(file_path):
        fresh = copy.deepcopy(DEFAULT_DATA)
        save_data(fresh)
        return fresh
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k, v in DEFAULT_DATA.items():
        if k not in data:
            data[k] = copy.deepcopy(v)
    return data

def save_data(data):
    user = _current_user()
    sh = _get_gsheet()
    if sh is not None:
        ws_name = f"data_{user}"[:30]
        try:
            ws = sh.worksheet(ws_name)
        except Exception:
            ws = sh.add_worksheet(title=ws_name, rows=10, cols=5)
        ws.update("A1", [[json.dumps(data, ensure_ascii=False)]])
        return

    file_path = f"user_data_{user}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_measurement(record: dict):
    data = load_data()
    record["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    data["measurements"].append(record)
    data["profile"]["weight"] = record["weight"]
    save_data(data)

def add_dish(dish: dict):
    data = load_data()
    data["dishes"].append(dish)
    save_data(data)

def get_day_diary(date_str: str) -> list:
    data = load_data()
    return data["diary_by_date"].get(date_str, [])

def save_day_diary(date_str: str, entries: list):
    data = load_data()
    data["diary_by_date"][date_str] = entries
    save_data(data)
def delete_user_data(username: str):
    sh = _get_gsheet()
    if sh is not None:
        ws_name = f"data_{username}"[:30]
        try:
            ws = sh.worksheet(ws_name)
            sh.del_worksheet(ws)
        except Exception:
            pass
        return

    file_path = f"user_data_{username}.json"
    if os.path.exists(file_path):
        os.remove(file_path)
def add_custom_ingredient(ing_dict: dict):
    data = load_data()
    if "custom_ingredients" not in data:
        data["custom_ingredients"] = []
    data["custom_ingredients"] = [
        x for x in data["custom_ingredients"]
        if x["name"].strip().lower() != ing_dict["name"].strip().lower()
    ]
    data["custom_ingredients"].append(ing_dict)
    save_data(data)
def delete_custom_ingredient(ing_name: str):
    data = load_data()
    if "custom_ingredients" in data:
        data["custom_ingredients"] = [
            x for x in data["custom_ingredients"]
            if x["name"].strip().lower() != ing_name.strip().lower()
        ]
        save_data(data)
