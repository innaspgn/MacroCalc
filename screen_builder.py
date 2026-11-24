import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from storage import add_dish, save_data, get_day_diary, save_day_diary
from menu_logic import build_ration_plan
from recipe_calculator import render_recipe_calculator

CATEGORIES = ["Завтрак", "Обед", "Ужин", "Перекус", "Десерт"]
COOK_TIMES = [10, 15, 20, 30, 40, 60]
SUB_TYPES = ["Не применимо", "Соленые", "Сладкие", "С выпечкой", "Шоколадные", "С охлаждением"]
PROTEIN_TYPES = ["Любой", "Мясо и птица", "Рыба и морепродукты", "Без мяса/рыбы"]

def show_builder_screen(data: dict, go_to):
    date_str = st.session_state.get("builder_date", datetime.now().strftime("%Y-%m-%d"))
    
    if st.button("Назад к рациону"):
        go_to("ration")
        
    st.subheader(f"Конструктор меню на {date_str}")

    tab_gen, tab_manual, tab_db, tab_calc = st.tabs([
        "Пересобрать день",
        "Добавить в день",
        "Книга блюд",
        "Калькулятор рецепта"
    ])

    with tab_gen:
        mode_choice = st.radio("Режим сборки:", ["Всё заново", "Добавить недостающие"], horizontal=True)
        mode_code = "all" if mode_choice == "Всё заново" else "missing"

        cook_time = st.selectbox(
            "Готовка не дольше:",
            ["Не важно", "10", "15", "20", "30", "40"],
            format_func=lambda x: f"{x} минут" if x != "Не важно" else "Не важно"
        )
        breakfast_type = st.radio("Завтраки:", ["Оба", "Соленые", "Сладкие"], horizontal=True)
        protein_type = st.radio("Белок (обед/ужин):", ["Любой", "Мясо и птица", "Рыба и морепродукты"], horizontal=True)
        dessert_type = st.selectbox("Десерты:", ["Любые", "С выпечкой", "Шоколадные", "С охлаждением"])
        allow_store_snacks = st.toggle("Готовые продукты из магазина в перекусах", value=True)
        cook_two_days = st.checkbox("Готовить на 2 дня (сохранить обед и ужин также на следующий день)", value=False)

        if len(data["dishes"]) == 0:
            st.warning("Ваша книга блюд пока пуста. Сначала добавьте блюда во вкладке «Книга блюд».")
        else:
            if st.button("Пересобрать день", type="primary", use_container_width=True):
                filters = {
                    "max_time": cook_time,
                    "breakfast_type": breakfast_type,
                    "protein_type": protein_type,
                    "dessert_type": dessert_type,
                    "allow_store_snacks": allow_store_snacks
                }
                existing = get_day_diary(date_str)
                new_plan = build_ration_plan(data["dishes"], data["targets"], existing, mode_code, filters)
                save_day_diary(date_str, new_plan)
                
                if cook_two_days:
                    next_date_obj = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)
                    next_date_str = next_date_obj.strftime("%Y-%m-%d")
                    next_day_entries = [e for e in get_day_diary(next_date_str) if e["meal"] not in ["Обед", "Ужин"]]
                    lunch_dinner = [e.copy() for e in new_plan if e["meal"] in ["Обед", "Ужин"]]
                    save_day_diary(next_date_str, next_day_entries + lunch_dinner)
                
                st.success("Рацион успешно пересобран")
                go_to("ration")
    with tab_manual:
        if not data["dishes"]:
            st.info("Сначала внесите блюда во вкладке «Книга блюд».")
        else:
            m_col1, m_col2 = st.columns([1.5, 1])
            m_search = m_col1.text_input(
                "Быстрый поиск блюда",
                placeholder="Начните вводить название...",
                key="manual_dish_search"
            )
            m_cat_filter = m_col2.selectbox(
                "Категория",
                ["Все категории"] + CATEGORIES,
                key="manual_dish_cat"
            )

            filtered_manual = data["dishes"]
            if m_cat_filter != "Все категории":
                filtered_manual = [d for d in filtered_manual if d.get("category") == m_cat_filter]
            if m_search.strip():
                q = m_search.strip().lower()
                filtered_manual = [d for d in filtered_manual if q in d["name"].lower()]

            if not filtered_manual:
                st.warning("По вашему запросу блюд не найдено.")
            else:
                dish_names = [d["name"] for d in filtered_manual]
                sel_dish_name = st.selectbox("Выберите готовое блюдо", dish_names)
                dish_obj = next(d for d in filtered_manual if d["name"] == sel_dish_name)
                
                meal_slot = st.selectbox(
                    "Прием пищи",
                    CATEGORIES,
                    index=CATEGORIES.index(dish_obj["category"]) if dish_obj["category"] in CATEGORIES else 0
                )
                grams = st.number_input("Вес порции (г)", min_value=10, max_value=2000, value=200, step=10)
                
                factor = grams / 100
                k = round(dish_obj["kcal"] * factor)
                p = round(dish_obj["protein"] * factor, 1)
                f = round(dish_obj["fat"] * factor, 1)
                c = round(dish_obj["carbs"] * factor, 1)
                
                st.caption(f"КБЖУ порции: {k} ккал | Белки: {p} г | Жиры: {f} г | Углеводы: {c} г")
                
                if st.button("Добавить в рацион дня", type="primary", use_container_width=True):
                    current_entries = get_day_diary(date_str)
                    current_entries.append({
                        "meal": meal_slot,
                        "name": sel_dish_name,
                        "grams": grams,
                        "kcal": k,
                        "protein": p,
                        "fat": f,
                        "carbs": c
                    })
                    save_day_diary(date_str, current_entries)
                    st.success("Блюдо добавлено в рацион")
                    go_to("ration")
    with tab_db:
        if "dish_form_key" not in st.session_state:
            st.session_state.dish_form_key = 0

        st.write("Внесите новое готовое блюдо (указывайте КБЖУ на 100 г готового блюда):")
        with st.form(f"add_dish_form_{st.session_state.dish_form_key}"):
            d_name = st.text_input("Название блюда", value="")
            d_cat = st.selectbox("Категория", CATEGORIES, index=0)
            d_time = st.selectbox("Время готовки (мин)", COOK_TIMES, index=2)
            d_store = st.checkbox("Это готовый продукт из магазина (для перекусов)", value=False)
            d_sub = st.selectbox("Тип (для завтраков и десертов)", SUB_TYPES, index=0)
            d_prot_type = st.selectbox("Основной белок (для обеда/ужина)", PROTEIN_TYPES, index=0)
            d_kcal = st.number_input("Ккал на 100 г", min_value=0.0, value=0.0, step=1.0)
            d_p = st.number_input("Белки на 100 г (г)", min_value=0.0, value=0.0, step=0.1)
            d_f = st.number_input("Жиры на 100 г (г)", min_value=0.0, value=0.0, step=0.1)
            d_c = st.number_input("Углеводы на 100 г (г)", min_value=0.0, value=0.0, step=0.1)
            
            if st.form_submit_button("Сохранить блюдо в мою книгу", use_container_width=True):
                if d_name.strip():
                    add_dish({
                        "name": d_name.strip(),
                        "category": d_cat,
                        "cook_time": d_time,
                        "is_store_bought": d_store,
                        "sub_type": d_sub,
                        "protein_type": d_prot_type,
                        "kcal": d_kcal,
                        "protein": d_p,
                        "fat": d_f,
                        "carbs": d_c
                    })
                    st.session_state.dish_form_key += 1
                    st.success(f"Блюдо «{d_name}» добавлено")
                    st.rerun()
                else:
                    st.error("Введите название блюда")

        if data["dishes"]:
            st.subheader("Сохраненные блюда")
            
            f_col1, f_col2 = st.columns([1.5, 1])
            search_query = f_col1.text_input("Быстрый поиск по названию", placeholder="Введите слово...")
            cat_filter = f_col2.selectbox("Фильтр по категории", ["Все категории"] + CATEGORIES)

            filtered_dishes = data["dishes"]
            if cat_filter != "Все категории":
                filtered_dishes = [d for d in filtered_dishes if d.get("category") == cat_filter]
            if search_query.strip():
                q = search_query.strip().lower()
                filtered_dishes = [d for d in filtered_dishes if q in d["name"].lower()]

            if filtered_dishes:
                df_dishes = pd.DataFrame(filtered_dishes).rename(columns={
                    "name": "Название", "category": "Категория", "cook_time": "Время (мин)",
                    "is_store_bought": "Из магазина", "sub_type": "Подтип", "protein_type": "Белок",
                    "kcal": "Ккал", "protein": "Белки", "fat": "Жиры", "carbs": "Углеводы"
                })
                st.dataframe(df_dishes, use_container_width=True, hide_index=True)
            else:
                st.info("По вашему запросу блюд не найдено.")

            st.subheader("Редактировать или удалить блюдо")
            dishes_list = data["dishes"]
            edit_idx = st.selectbox(
                "Выберите блюдо для изменения:",
                list(range(len(dishes_list))),
                format_func=lambda i: f"{dishes_list[i]['name']} ({dishes_list[i]['category']} — {dishes_list[i]['kcal']} ккал)"
            )
            target_dish = dishes_list[edit_idx]

            with st.form("edit_dish_form"):
                e_name = st.text_input("Название блюда", value=target_dish["name"])
                e_cat = st.selectbox("Категория", CATEGORIES, index=CATEGORIES.index(target_dish["category"]) if target_dish["category"] in CATEGORIES else 0)
                e_time = st.selectbox("Время готовки (мин)", COOK_TIMES, index=COOK_TIMES.index(target_dish.get("cook_time", 20)) if target_dish.get("cook_time", 20) in COOK_TIMES else 2)
                e_store = st.checkbox("Готовый продукт из магазина", value=target_dish.get("is_store_bought", False))
                e_sub = st.selectbox("Тип (завтраки и десерты)", SUB_TYPES, index=SUB_TYPES.index(target_dish.get("sub_type", "Не применимо")) if target_dish.get("sub_type", "Не применимо") in SUB_TYPES else 0)
                e_prot = st.selectbox("Основной белок", PROTEIN_TYPES, index=PROTEIN_TYPES.index(target_dish.get("protein_type", "Любой")) if target_dish.get("protein_type", "Любой") in PROTEIN_TYPES else 0)
                e_kcal = st.number_input("Ккал на 100 г", min_value=0.0, value=float(target_dish["kcal"]), step=1.0)
                e_p = st.number_input("Белки на 100 г (г)", min_value=0.0, value=float(target_dish["protein"]), step=0.1)
                e_f = st.number_input("Жиры на 100 г (г)", min_value=0.0, value=float(target_dish["fat"]), step=0.1)
                e_c = st.number_input("Углеводы на 100 г (г)", min_value=0.0, value=float(target_dish["carbs"]), step=0.1)

                if st.form_submit_button("Сохранить изменения", use_container_width=True):
                    if e_name.strip():
                        data["dishes"][edit_idx] = {
                            "name": e_name.strip(), "category": e_cat, "cook_time": e_time,
                            "is_store_bought": e_store, "sub_type": e_sub, "protein_type": e_prot,
                            "kcal": e_kcal, "protein": e_p, "fat": e_f, "carbs": e_c
                        }
                        save_data(data)
                        st.success("Изменения сохранены")
                        st.rerun()

            if st.button("Удалить выбранное блюдо из книги"):
                data["dishes"].pop(edit_idx)
                save_data(data)
                st.success("Блюдо удалено")
                st.rerun()

    with tab_calc:
        render_recipe_calculator()
