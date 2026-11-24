import streamlit as st
import pandas as pd
import plotly.express as px
from storage import add_measurement, save_data, delete_user_data
from nutrition_logic import calculate_bmi
from auth import update_user_credentials, delete_user_account

FIELD_LABELS = {
    "date": "Дата замера",
    "weight": "Вес (кг)",
    "chest": "Обхват груди (см)",
    "under_chest": "Под грудью (см)",
    "waist": "Талия (см)",
    "hips": "Бедра (см)",
    "thigh_left": "Левая ляжка (см)",
    "thigh_right": "Правая ляжка (см)",
    "arm": "Рука (см)",
    "note": "Заметка о самочувствии"
}

def show_profile_screen(data: dict, go_to):
    if st.button("Вернуться к рациону"):
        go_to("ration")
        
    st.subheader("Мой профиль и динамика параметров")
    p = data["profile"]
    bmi, bmi_status = calculate_bmi(p["weight"], p["height"])
    
    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.metric("Текущий вес", f"{p['weight']} кг")
        c2.metric("Рост и возраст", f"{p['height']} см / {p['age']} лет")
        c3, c4 = st.columns(2)
        c3.metric("Индекс массы тела (ИМТ)", f"{bmi} ({bmi_status})")
        c4.metric("Цель от тренировок", p["goal"])

    st.divider()
    with st.expander("Записать новые замеры тела"):
        with st.form("profile_new_measure"):
            w = st.number_input("Вес (кг)", value=float(p["weight"]), step=0.1)
            chest = st.number_input("Обхват груди (см)", min_value=0.0, step=0.5)
            under_chest = st.number_input("Под грудью (см)", min_value=0.0, step=0.5)
            waist = st.number_input("Талия (см)", min_value=0.0, step=0.5)
            hips = st.number_input("Бедра (см)", min_value=0.0, step=0.5)
            thigh_l = st.number_input("Левая ляжка (см)", min_value=0.0, step=0.5)
            thigh_r = st.number_input("Правая ляжка (см)", min_value=0.0, step=0.5)
            arm = st.number_input("Рука (см)", min_value=0.0, step=0.5)
            note = st.text_input("Заметка о самочувствии (например: после тренировки, день цикла, отек)")
            
            if st.form_submit_button("Сохранить замеры", use_container_width=True):
                add_measurement({
                    "weight": w, "chest": chest, "under_chest": under_chest,
                    "waist": waist, "hips": hips, "thigh_left": thigh_l,
                    "thigh_right": thigh_r, "arm": arm, "note": note.strip()
                })
                st.success("Замеры и заметка сохранены")
                st.rerun()

    if data["measurements"]:
        st.subheader("История замеров")
        df_m = pd.DataFrame(data["measurements"])
        if "note" not in df_m.columns:
            df_m["note"] = ""
        cols_order = ["date", "weight", "chest", "under_chest", "waist", "hips", "thigh_left", "thigh_right", "arm", "note"]
        existing_cols = [c for c in cols_order if c in df_m.columns]
        df_ru = df_m[existing_cols].rename(columns=FIELD_LABELS)
        
        st.dataframe(df_ru, use_container_width=True, hide_index=True)
        
        if len(df_m) > 1:
            st.subheader("График изменения параметра")
            plot_options = [c for c in cols_order if c not in ["date", "note"] and c in df_m.columns]
            selected_key = st.selectbox(
                "Выберите параметр для графика:",
                plot_options,
                format_func=lambda k: FIELD_LABELS[k]
            )
            fig = px.line(
                df_ru,
                x="Дата замера",
                y=FIELD_LABELS[selected_key],
                hover_data=["Заметка о самочувствии"],
                markers=True,
                title=f"Динамика: {FIELD_LABELS[selected_key]}"
            )
            fig.update_traces(line_color="#7D5A73", marker_color="#9C6B84")
            fig.update_layout(plot_bgcolor="#FAF6F2", paper_bgcolor="#F7F3EE")
            st.plotly_chart(fig, use_container_width=True)
            
        st.divider()
        with st.expander("Удаление отдельного замера"):
            records = data["measurements"]
            options_idx = list(range(len(records)))
            del_idx = st.selectbox(
                "Выберите запись для удаления:",
                options_idx,
                format_func=lambda i: f"{records[i]['date']} — Вес: {records[i]['weight']} кг ({records[i].get('note', '')})"
            )
            if st.button("Удалить выбранный замер"):
                records.pop(del_idx)
                data["measurements"] = records
                save_data(data)
                st.success("Запись удалена")
                st.rerun()

    st.divider()
    with st.expander("Настройки аккаунта (имя и пароль)"):
        with st.form("account_settings_form"):
            curr_name = st.session_state.get("display_name", "")
            new_name = st.text_input("Отображаемое имя", value=curr_name)
            new_pwd = st.text_input("Новый пароль (оставьте пустым, если не меняете)", type="password")
            confirm_pwd = st.text_input("Повторите новый пароль", type="password")
            
            if st.form_submit_button("Обновить данные аккаунта", use_container_width=True):
                if new_pwd and new_pwd != confirm_pwd:
                    st.error("Новые пароли не совпадают")
                else:
                    ok, msg = update_user_credentials(st.session_state.current_user, new_name, new_pwd)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.divider()
    with st.expander("Удаление профиля"):
        st.warning("Внимание: будут безвозвратно удалены ваш аккаунт, замеры, книга блюд и весь дневник питания.")
        confirm_del = st.checkbox("Я подтверждаю полное удаление моего профиля")
        if st.button("Удалить профиль навсегда", disabled=not confirm_del):
            uname = st.session_state.current_user
            delete_user_data(uname)
            delete_user_account(uname)
            st.session_state.clear()
            st.rerun()
