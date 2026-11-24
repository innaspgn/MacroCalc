import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timezone, timedelta
from storage import save_data, get_day_diary, save_day_diary

def show_ration_screen(data: dict, go_to):
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("Мой профиль и замеры", use_container_width=True):
            go_to("profile")
    with col_nav2:
        if st.button("Пересчитать КБЖУ", use_container_width=True):
            go_to("calc")

    local_today = (datetime.now(timezone.utc) + timedelta(hours=5)).date()
    selected_date = st.date_input("Выберите дату рациона", value=local_today)
    date_str = selected_date.strftime("%Y-%m-%d")

    if data.get("targets_changed"):
        with st.container(border=True):
            st.warning("Целевое КБЖУ изменилось. Хотите пересобрать рацион под новую норму?")
            if st.button("Пересобрать", type="primary", use_container_width=True):
                data["targets_changed"] = False
                save_data(data)
                st.session_state.builder_date = date_str
                go_to("builder")
            if st.button("Не сейчас"):
                data["targets_changed"] = False
                save_data(data)
                st.rerun()

    targets = data["targets"]
    day_entries = get_day_diary(date_str)
    
    eaten_kcal = sum(item["kcal"] for item in day_entries)
    eaten_p = round(sum(item["protein"] for item in day_entries), 1)
    eaten_f = round(sum(item["fat"] for item in day_entries), 1)
    eaten_c = round(sum(item["carbs"] for item in day_entries), 1)

    st.subheader(f"Норма на {date_str}")
    progress_val = min(eaten_kcal / max(targets["kcal"], 1), 1.0)
    st.progress(progress_val, text=f"Выполнено: {eaten_kcal} из {targets['kcal']} ккал ({round(progress_val * 100)}%)")
    
    with st.container(border=True):
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Калории", f"{eaten_kcal} / {targets['kcal']}", f"Осталось: {targets['kcal'] - eaten_kcal}")
        m2.metric("Белки", f"{eaten_p} / {targets['protein']} г")
        m3.metric("Жиры", f"{eaten_f} / {targets['fat']} г")
        m4.metric("Углеводы", f"{eaten_c} / {targets['carbs']} г")

    st.subheader("Ваш рацион на этот день")
    if day_entries:
        for idx, entry in enumerate(day_entries):
            with st.container(border=True):
                st.markdown(
                    f"**{entry['meal']}**: {entry['name']} — {entry['grams']} г  \n"
                    f"{entry['kcal']} ккал | Белки: {entry['protein']} г | Жиры: {entry['fat']} г | Углеводы: {entry['carbs']} г"
                )
                if st.button("Удалить блюдо из дня", key=f"del_{date_str}_{idx}"):
                    day_entries.pop(idx)
                    save_day_diary(date_str, day_entries)
                    st.rerun()

        with st.expander("Скопировать весь день или отдельное блюдо на другую дату"):
            copy_mode = st.radio(
                "Что скопировать?",
                ["Весь рацион дня", "Одно выбранное блюдо"],
                horizontal=True
            )
            dish_to_copy = None
            if copy_mode == "Одно выбранное блюдо":
                sel_idx = st.selectbox(
                    "Выберите блюдо:",
                    list(range(len(day_entries))),
                    format_func=lambda i: f"{day_entries[i]['meal']}: {day_entries[i]['name']} ({day_entries[i]['grams']} г)"
                )
                dish_to_copy = day_entries[sel_idx].copy()

            target_copy_date = st.date_input(
                "На какую дату скопировать?",
                value=selected_date + timedelta(days=1),
                key=f"copy_date_{date_str}"
            )
            target_date_str = target_copy_date.strftime("%Y-%m-%d")

            if st.button("Скопировать на выбранную дату", type="primary", use_container_width=True):
                existing_target = get_day_diary(target_date_str)
                if copy_mode == "Весь рацион дня":
                    copied_items = [item.copy() for item in day_entries]
                    save_day_diary(target_date_str, existing_target + copied_items)
                    st.success(f"Весь рацион скопирован на {target_date_str}")
                else:
                    existing_target.append(dish_to_copy)
                    save_day_diary(target_date_str, existing_target)
                    st.success(f"Блюдо «{dish_to_copy['name']}» скопировано на {target_date_str}")
    else:
        st.info("На эту дату пока нет добавленных блюд.")

    st.write("")
    if st.button("Пересобрать / Добавить готовое блюдо", type="primary", use_container_width=True):
        st.session_state.builder_date = date_str
        go_to("builder")

    if "open_shop_list" not in st.session_state:
        st.session_state.open_shop_list = False
    if "open_week_dash" not in st.session_state:
        st.session_state.open_week_dash = False

    st.write("")
    col_shop, col_dash = st.columns(2)
    with col_shop:
        if st.button("Автоматический список продуктов", use_container_width=True):
            st.session_state.open_shop_list = not st.session_state.open_shop_list
            st.session_state.open_week_dash = False
    with col_dash:
        if st.button("Недельный дашборд выполнения", use_container_width=True):
            st.session_state.open_week_dash = not st.session_state.open_week_dash
            st.session_state.open_shop_list = False

    if st.session_state.open_shop_list:
        with st.container(border=True):
            st.caption("Выберите диапазон дат — сайт суммирует все блюда из вашего рациона на эти дни.")
            c_d1, c_d2 = st.columns(2)
            shop_start = c_d1.date_input("С даты", value=selected_date, key="shop_start")
            shop_end = c_d2.date_input("По дату", value=selected_date + timedelta(days=2), key="shop_end")

            if shop_end < shop_start:
                st.error("Конечная дата не может быть раньше начальной")
            else:
                totals_by_item = {}
                curr_d = shop_start
                while curr_d <= shop_end:
                    d_entries = get_day_diary(curr_d.strftime("%Y-%m-%d"))
                    for item in d_entries:
                        name = item["name"]
                        totals_by_item[name] = totals_by_item.get(name, 0) + item["grams"]
                    curr_d += timedelta(days=1)

                if not totals_by_item:
                    st.info("На выбранные даты в рационе пока нет блюд.")
                else:
                    st.markdown("**Чек-лист покупок / заготовок:**")
                    text_lines = []
                    for idx, (b_name, total_g) in enumerate(sorted(totals_by_item.items())):
                        label = f"{b_name} — {round(total_g)} г"
                        st.checkbox(label, key=f"shop_chk_{shop_start}_{shop_end}_{idx}")
                        text_lines.append(f"- {label}")

                    st.text_area(
                        "Текст списка (можно скопировать в заметки):",
                        value="\n".join(text_lines),
                        height=130
                    )

    if st.session_state.open_week_dash:
        with st.container(border=True):
            week_rows = []
            for offset in range(6, -1, -1):
                d_obj = selected_date - timedelta(days=offset)
                d_s = d_obj.strftime("%Y-%m-%d")
                entries = get_day_diary(d_s)
                week_rows.append({
                    "Дата": d_obj.strftime("%d.%m"),
                    "Калории": sum(x["kcal"] for x in entries),
                    "Белки": round(sum(x["protein"] for x in entries), 1),
                    "Жиры": round(sum(x["fat"] for x in entries), 1),
                    "Углеводы": round(sum(x["carbs"] for x in entries), 1)
                })
            df_week = pd.DataFrame(week_rows)

            avg_kcal = round(df_week["Калории"].mean())
            st.caption(f"Средняя калорийность за 7 дней: {avg_kcal} ккал (цель: {targets['kcal']} ккал)")

            fig = px.bar(
                df_week,
                x="Дата",
                y="Калории",
                text="Калории",
                title="Калорийность за последние 7 дней"
            )
            fig.update_traces(marker_color="#9C6B84", textposition="outside")
            fig.add_hline(
                y=targets["kcal"],
                line_dash="dash",
                line_color="#4A313D",
                annotation_text=f"Цель: {targets['kcal']} ккал"
            )
            fig.update_layout(
                plot_bgcolor="#FAF6F2",
                paper_bgcolor="#EFE7DF",
                yaxis_range=[0, max(df_week["Калории"].max(), targets["kcal"]) * 1.2]
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(df_week, use_container_width=True, hide_index=True)
