import streamlit as st
from storage import save_data, add_measurement, load_data
from nutrition_logic import calculate_bmi, calculate_targets, ACTIVITY_MULTIPLIERS

def show_calc_screen(data: dict, go_to):
    st.subheader("Расчет параметров и цели")
    
    gender_list = ["Женский", "Мужской"]
    curr_gender = data["profile"].get("gender", "Женский")
    gender = st.radio(
        "Пол",
        gender_list,
        index=gender_list.index(curr_gender) if curr_gender in gender_list else 0,
        horizontal=True
    )
    
    age = st.number_input("Возраст (лет)", min_value=14, max_value=100, value=int(data["profile"]["age"]))
    height = st.number_input("Рост (см)", min_value=120, max_value=230, value=int(data["profile"]["height"]))
    weight = st.number_input("Текущий вес (кг)", min_value=30.0, max_value=250.0, value=float(data["profile"]["weight"]), step=0.1)
    
    bmi, bmi_status = calculate_bmi(weight, height)
    st.info(f"Ваш текущий ИМТ: **{bmi}** ({bmi_status})")

    goals_list = ["Сушка", "Рекомпозиция", "Набор"]
    curr_goal = data["profile"]["goal"]
    goal = st.selectbox("Ваша цель от тренировок", goals_list, index=goals_list.index(curr_goal) if curr_goal in goals_list else 1)
    
    act_keys = list(ACTIVITY_MULTIPLIERS.keys())
    curr_act = data["profile"]["activity"]
    activity = st.selectbox("Дневная активность", act_keys, index=act_keys.index(curr_act) if curr_act in act_keys else 2)
    
    hormones_list = ["Нет особенностей", "Гипотиреоз", "Инсулинорезистентность / СПКЯ", "Другое"]
    curr_h = data["profile"].get("hormones", "Нет особенностей")
    hormones = st.selectbox("Есть ли гормональные нарушения?", hormones_list, index=hormones_list.index(curr_h) if curr_h in hormones_list else 0)
    
    takes_meds = st.checkbox("Я принимаю гормональные или иные препараты", value=data["profile"].get("takes_meds", False))
    if takes_meds:
        st.warning("Если вы принимаете препараты, перед началом тренировок и изменением питания необходимо проконсультироваться с врачом.")

    st.divider()
    if st.button("Рассчитать", type="primary", use_container_width=True):
        data["profile"].update({
            "gender": gender,
            "age": age,
            "height": height,
            "weight": weight,
            "goal": goal,
            "activity": activity,
            "hormones": hormones,
            "takes_meds": takes_meds
        })
        save_data(data)
        st.session_state.temp_targets = calculate_targets(data["profile"])
        st.session_state.manual_mode = False
        go_to("measurements")
        
    if st.button("Или введите свое целевое КБЖУ", use_container_width=True):
        data["profile"].update({
            "gender": gender,
            "age": age,
            "height": height,
            "weight": weight,
            "goal": goal,
            "activity": activity,
            "hormones": hormones,
            "takes_meds": takes_meds
        })
        save_data(data)
        st.session_state.manual_mode = True
        go_to("measurements")


def show_measurements_screen(data: dict, go_to):
    st.subheader("Замеры параметров тела")
    st.caption("Заполните текущие объемы, чтобы в дальнейшем отслеживать динамику в профиле.")
    
    with st.form("wizard_measurements"):
        w = st.number_input("Вес (кг)", value=float(data["profile"]["weight"]), step=0.1)
        chest = st.number_input("Обхват груди (см)", min_value=0.0, step=0.5)
        under_chest = st.number_input("Под грудью (см)", min_value=0.0, step=0.5)
        waist = st.number_input("Талия (см)", min_value=0.0, step=0.5)
        hips = st.number_input("Бедра (см)", min_value=0.0, step=0.5)
        thigh_l = st.number_input("Левая ляжка (см)", min_value=0.0, step=0.5)
        thigh_r = st.number_input("Правая ляжка (см)", min_value=0.0, step=0.5)
        arm = st.number_input("Рука (см)", min_value=0.0, step=0.5)
        
        if st.form_submit_button("Сохранить параметры и перейти к норме КБЖУ", use_container_width=True):
            add_measurement({
                "weight": w,
                "chest": chest,
                "under_chest": under_chest,
                "waist": waist,
                "hips": hips,
                "thigh_left": thigh_l,
                "thigh_right": thigh_r,
                "arm": arm
            })
            if not st.session_state.manual_mode:
                fresh_data = load_data()
                st.session_state.temp_targets = calculate_targets(fresh_data["profile"])
            go_to("summary")


def show_summary_screen(data: dict, go_to):
    st.subheader("Ваша целевая норма КБЖУ")
    
    if st.session_state.manual_mode:
        st.write("Введите ваши целевые значения вручную:")
        m_kcal = st.number_input("Калории (ккал)", min_value=800, max_value=6000, value=int(data["targets"]["kcal"]), step=50)
        m_p = st.number_input("Белки (г)", min_value=20, max_value=400, value=int(data["targets"]["protein"]), step=5)
        m_f = st.number_input("Жиры (г)", min_value=20, max_value=250, value=int(data["targets"]["fat"]), step=5)
        m_c = st.number_input("Углеводы (г)", min_value=20, max_value=700, value=int(data["targets"]["carbs"]), step=5)
        st.session_state.temp_targets = {"kcal": m_kcal, "protein": m_p, "fat": m_f, "carbs": m_c}
    else:
        t = st.session_state.temp_targets
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Калории", f"{t['kcal']} ккал")
            c2.metric("Белки", f"{t['protein']} г")
            c3.metric("Жиры", f"{t['fat']} г")
            c4.metric("Углеводы", f"{t['carbs']} г")
        
        if data["profile"].get("goal") == "Рекомпозиция":
            min_def = round(t['kcal'] * 0.90)
            max_def = round(t['kcal'] * 0.95)
            st.info(
                f"Памятка для рекомпозиции: чтобы плавно снижать вес без потери мышечной массы, "
                f"от данного калоража рекомендуется вычесть 5–10% — ваш ориентир для мягкого дефицита составит {min_def}–{max_def} ккал."
            )

    st.divider()
    if "norm_saved" not in st.session_state:
        st.session_state.norm_saved = False

    if not st.session_state.norm_saved:
        if st.button("Сохранить свою норму", type="primary", use_container_width=True):
            old_targets = data.get("targets", {})
            new_targets = st.session_state.temp_targets
            if data.get("onboarded") and old_targets != new_targets:
                data["targets_changed"] = True
            data["targets"] = new_targets
            data["onboarded"] = True
            save_data(data)
            st.session_state.norm_saved = True
            st.rerun()
        if st.button("Пересчитать", use_container_width=True):
            go_to("calc")
    else:
        st.success("Норма КБЖУ успешно сохранена")
        if st.button("К рациону", type="primary", use_container_width=True):
            st.session_state.norm_saved = False
            go_to("ration")
        if st.button("Открыть профиль", use_container_width=True):
            st.session_state.norm_saved = False
            go_to("profile")
        if st.button("Пересчитать", use_container_width=True):
            st.session_state.norm_saved = False
            go_to("calc")
