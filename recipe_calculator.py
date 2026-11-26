import streamlit as st
import pandas as pd
from storage import add_dish
from base_products import BASE_PRODUCTS

CATEGORIES = ["Завтрак", "Обед", "Ужин", "Перекус", "Десерт"]
COOK_TIMES = [10, 15, 20, 30, 40, 60]
SUB_TYPES = ["Не применимо", "Соленые", "Сладкие", "С выпечкой", "Шоколадные", "С охлаждением"]
PROTEIN_TYPES = ["Любой", "Мясо и птица", "Рыба и морепродукты", "Без мяса/рыбы"]

def render_recipe_calculator():
    st.caption("Соберите блюдо из сырых ингредиентов, укажите итоговый вес после готовки — и калькулятор сам посчитает точное КБЖУ на 100 г.")

    if "recipe_ingredients" not in st.session_state:
        st.session_state.recipe_ingredients = []
    if "ing_form_key" not in st.session_state:
        st.session_state.ing_form_key = 0

    with st.container(border=True):
        st.subheader("Добавить ингредиент в рецепт")

        template_options = ["— Ввести вручную —"] + [
            f"{item['name']} ({item['kcal']} ккал | Б:{item['p']} Ж:{item['f']} У:{item['c']})"
            for item in BASE_PRODUCTS
        ]
        selected_tpl = st.selectbox(
            "Быстрый выбор из справочника (начните вводить название):",
            template_options,
            key=f"tpl_select_{st.session_state.ing_form_key}"
        )

        default_name = ""
        default_kcal = 0.0
        default_p = 0.0
        default_f = 0.0
        default_c = 0.0

        if selected_tpl != "— Ввести вручную —":
            tpl_idx = template_options.index(selected_tpl) - 1
            chosen = BASE_PRODUCTS[tpl_idx]
            default_name = chosen["name"]
            default_kcal = float(chosen["kcal"])
            default_p = float(chosen["p"])
            default_f = float(chosen["f"])
            default_c = float(chosen["c"])

        fk = f"{st.session_state.ing_form_key}_{template_options.index(selected_tpl)}"

        ing_name = st.text_input("Название ингредиента", value=default_name, key=f"name_{fk}")
        ing_weight = st.number_input("Вес ингредиента (г)", min_value=1.0, value=100.0, step=5.0, key=f"weight_{fk}")
        c1, c2 = st.columns(2)
        ing_kcal = c1.number_input("Ккал на 100 г продукта", min_value=0.0, value=default_kcal, step=1.0, key=f"kcal_{fk}")
        ing_p = c2.number_input("Белки на 100 г (г)", min_value=0.0, value=default_p, step=0.1, key=f"p_{fk}")
        ing_f = c1.number_input("Жиры на 100 г (г)", min_value=0.0, value=default_f, step=0.1, key=f"f_{fk}")
        ing_c = c2.number_input("Углеводы на 100 г (г)", min_value=0.0, value=default_c, step=0.1, key=f"c_{fk}")

        factor = ing_weight / 100.0
        st.caption(
            f"На {ing_weight:g} г получится: **{round(ing_kcal * factor, 1)} ккал** | "
            f"Белки: **{round(ing_p * factor, 1)} г** | "
            f"Жиры: **{round(ing_f * factor, 1)} г** | "
            f"Углеводы: **{round(ing_c * factor, 1)} г**"
        )

        if st.button("Добавить ингредиент в список", type="primary", use_container_width=True, key=f"btn_{st.session_state.ing_form_key}"):
            if ing_name.strip():
                st.session_state.recipe_ingredients.append({
                    "Ингредиент": ing_name.strip(),
                    "Вес (г)": ing_weight,
                    "Ккал": round(ing_kcal * factor, 1),
                    "Белки": round(ing_p * factor, 1),
                    "Жиры": round(ing_f * factor, 1),
                    "Углеводы": round(ing_c * factor, 1)
                })
                st.session_state.ing_form_key += 1
                st.rerun()
            else:
                st.error("Введите название ингредиента")
    if st.session_state.recipe_ingredients:
        st.subheader("Состав вашего рецепта")
        df_ing = pd.DataFrame(st.session_state.recipe_ingredients)
        st.dataframe(df_ing, use_container_width=True, hide_index=True)

        col_del_ing, col_clear_all = st.columns([2, 1])
        del_ing_idx = col_del_ing.selectbox(
            "Удалить ингредиент:",
            list(range(len(st.session_state.recipe_ingredients))),
            format_func=lambda i: f"{st.session_state.recipe_ingredients[i]['Ингредиент']} ({st.session_state.recipe_ingredients[i]['Вес (г)']} г)"
        )
        if col_del_ing.button("Удалить выбранный"):
            st.session_state.recipe_ingredients.pop(del_ing_idx)
            st.rerun()
        if col_clear_all.button("Очистить весь рецепт"):
            st.session_state.recipe_ingredients = []
            st.rerun()

        raw_weight = sum(x["Вес (г)"] for x in st.session_state.recipe_ingredients)
        total_kcal = sum(x["Ккал"] for x in st.session_state.recipe_ingredients)
        total_p = sum(x["Белки"] for x in st.session_state.recipe_ingredients)
        total_f = sum(x["Жиры"] for x in st.session_state.recipe_ingredients)
        total_c = sum(x["Углеводы"] for x in st.session_state.recipe_ingredients)

        st.write(f"**Общий вес сырых продуктов:** {round(raw_weight)} г")
        cooked_weight = st.number_input(
            "Итоговый вес готового блюда после уварки/ужарки (г):",
            min_value=10.0,
            value=float(round(raw_weight)),
            step=10.0,
            key=f"cooked_w_{round(raw_weight, 1)}"
        )

        final_kcal = round((total_kcal / cooked_weight) * 100, 1)
        final_p = round((total_p / cooked_weight) * 100, 1)
        final_f = round((total_f / cooked_weight) * 100, 1)
        final_c = round((total_c / cooked_weight) * 100, 1)

        with st.container(border=True):
            st.markdown("**Итоговое КБЖУ на 100 г готового блюда:**")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Ккал", f"{final_kcal}")
            m2.metric("Белки", f"{final_p} г")
            m3.metric("Жиры", f"{final_f} г")
            m4.metric("Углеводы", f"{final_c} г")

        with st.form("save_calculated_recipe"):
            st.subheader("Сохранить готовое блюдо в мою книгу")
            r_name = st.text_input("Название готового блюда (например: Сырники домашние)")
            r_cat = st.selectbox("Категория", CATEGORIES)
            r_time = st.selectbox("Время готовки (мин)", COOK_TIMES, index=2)
            r_sub = st.selectbox("Тип (для завтраков и десертов)", SUB_TYPES)
            r_prot = st.selectbox("Основной белок (для обеда/ужина)", PROTEIN_TYPES)

            if st.form_submit_button("Сохранить рецепт в книгу блюд", type="primary", use_container_width=True):
                if r_name.strip():
                    add_dish({
                        "name": r_name.strip(),
                        "category": r_cat,
                        "cook_time": r_time,
                        "is_store_bought": False,
                        "sub_type": r_sub,
                        "protein_type": r_prot,
                        "kcal": final_kcal,
                        "protein": final_p,
                        "fat": final_f,
                        "carbs": final_c
                    })
                    st.session_state.recipe_ingredients = []
                    st.success(f"Блюдо «{r_name.strip()}» успешно сохранено в вашу книгу блюд")
                    st.rerun()
                else:
                    st.error("Укажите название готового блюда")
