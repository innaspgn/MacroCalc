import streamlit as st
import pandas as pd
from storage import add_dish

CATEGORIES = ["Завтрак", "Обед", "Ужин", "Перекус", "Десерт"]
COOK_TIMES = [5, 10, 15, 20, 30, 40, 50, 60]
SUB_TYPES = ["Не применимо", "Соленые", "Сладкие", "С выпечкой", "Шоколадные", "С охлаждением"]
PROTEIN_TYPES = ["Любой", "Мясо и птица", "Рыба и морепродукты", "Без мяса/рыбы"]

def render_recipe_calculator():
    st.write("Соберите блюдо из сырых ингредиентов, укажите итоговый вес после готовки — и калькулятор сам посчитает точное КБЖУ на 100 г.")

    if "recipe_ingredients" not in st.session_state:
        st.session_state.recipe_ingredients = []

    with st.container(border=True):
        st.markdown("**Добавить ингредиент в рецепт**")
        ing_name = st.text_input("Название ингредиента (например: Куриное филе, Гречка сухая)", key="ing_name")
        ing_grams = st.number_input("Вес ингредиента (г)", min_value=1.0, value=100.0, step=10.0, key="ing_grams")
        
        c1, c2 = st.columns(2)
        ing_kcal = c1.number_input("Ккал на 100 г продукта", min_value=0.0, step=1.0, key="ing_kcal")
        ing_p = c2.number_input("Белки на 100 г (г)", min_value=0.0, step=0.1, key="ing_p")
        
        c3, c4 = st.columns(2)
        ing_f = c3.number_input("Жиры на 100 г (г)", min_value=0.0, step=0.1, key="ing_f")
        ing_c = c4.number_input("Углеводы на 100 г (г)", min_value=0.0, step=0.1, key="ing_c")

        if st.button("Добавить ингредиент в список", use_container_width=True):
            if ing_name.strip():
                factor = ing_grams / 100
                st.session_state.recipe_ingredients.append({
                    "Ингредиент": ing_name.strip(),
                    "Вес (г)": ing_grams,
                    "Ккал": round(ing_kcal * factor, 1),
                    "Белки": round(ing_p * factor, 1),
                    "Жиры": round(ing_f * factor, 1),
                    "Углеводы": round(ing_c * factor, 1)
                })
                st.rerun()
            else:
                st.error("Введите название ингредиента")

    ingredients = st.session_state.recipe_ingredients
    if ingredients:
        st.subheader("Состав рецепта")
        df_ing = pd.DataFrame(ingredients)
        st.dataframe(df_ing, use_container_width=True, hide_index=True)

        if st.button("Очистить список ингредиентов"):
            st.session_state.recipe_ingredients = []
            st.rerun()

        raw_total_weight = sum(x["Вес (г)"] for x in ingredients)
        total_kcal = sum(x["Ккал"] for x in ingredients)
        total_p = sum(x["Белки"] for x in ingredients)
        total_f = sum(x["Жиры"] for x in ingredients)
        total_c = sum(x["Углеводы"] for x in ingredients)

        st.divider()
        final_weight = st.number_input(
            f"Итоговый вес готового блюда после варки/запекания (г) — сырой вес был {round(raw_total_weight)} г:",
            min_value=10.0,
            value=float(round(raw_total_weight)),
            step=10.0
        )

        # Пересчет на 100 г готового блюда
        ratio = 100.0 / final_weight
        per100_kcal = round(total_kcal * ratio, 1)
        per100_p = round(total_p * ratio, 1)
        per100_f = round(total_f * ratio, 1)
        per100_c = round(total_c * ratio, 1)

        with st.container(border=True):
            st.markdown("**Итоговое КБЖУ на 100 г готового блюда:**")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Ккал", f"{per100_kcal}")
            m2.metric("Белки", f"{per100_p} г")
            m3.metric("Жиры", f"{per100_f} г")
            m4.metric("Углеводы", f"{per100_c} г")

        st.divider()
        with st.form("save_calculated_recipe"):
            r_name = st.text_input("Название готового блюда для сохранения в книгу")
            r_cat = st.selectbox("Категория", CATEGORIES)
            r_time = st.selectbox("Время готовки (мин)", COOK_TIMES, index=3)
            r_sub = st.selectbox("Тип (для завтраков и десертов)", SUB_TYPES)
            r_prot = st.selectbox("Основной белок (для обеда/ужина)", PROTEIN_TYPES)

            if st.form_submit_button("Сохранить готовое блюдо в мою книгу", use_container_width=True):
                if r_name.strip():
                    add_dish({
                        "name": r_name.strip(),
                        "category": r_cat,
                        "cook_time": r_time,
                        "is_store_bought": False,
                        "sub_type": r_sub,
                        "protein_type": r_prot,
                        "kcal": per100_kcal,
                        "protein": per100_p,
                        "fat": per100_f,
                        "carbs": per100_c
                    })
                    st.session_state.recipe_ingredients = []
                    st.success(f"Блюдо «{r_name}» с точным КБЖУ сохранено в вашу книгу!")
                    st.rerun()
                else:
                    st.error("Введите название блюда")
