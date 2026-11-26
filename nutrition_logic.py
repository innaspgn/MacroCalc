ACTIVITY_MULTIPLIERS = {
    "Минимальная (сидячий образ жизни, нет тренировок)": 1.2,
    "Низкая (1–2 легкие тренировки в неделю)": 1.375,
    "Средняя (3–4 тренировки в неделю)": 1.55,
    "Высокая (5–6 интенсивных тренировок в неделю)": 1.725,
    "Экстремальная (ежедневные тренировки / физический труд)": 1.9
}

def calculate_bmi(weight: float, height: float) -> tuple:
    h_m = height / 100.0
    bmi = round(weight / (h_m ** 2), 1)
    if bmi < 18.5:
        status = "Недостаток веса"
    elif bmi < 25.0:
        status = "Норма"
    elif bmi < 30.0:
        status = "Избыточный вес"
    else:
        status = "Ожирение"
    return bmi, status

def calculate_targets(profile_or_gender, age=None, height=None, weight=None, activity=None, goal=None) -> dict:
    if isinstance(profile_or_gender, dict):
        p = profile_or_gender
        gender = p.get("gender", "Женский")
        age = int(p.get("age", 25))
        height = float(p.get("height", 170))
        weight = float(p.get("weight", 64.0))
        activity = p.get("activity", "Низкая (1–2 легкие тренировки в неделю)")
        goal = p.get("goal", "Поддержание веса")
    else:
        gender = profile_or_gender

    if gender == "Женский":
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5

    mult = ACTIVITY_MULTIPLIERS.get(activity, 1.375)
    tdee = bmr * mult
    g = str(goal).lower()

    if "сушка" in g:
        kcal = round(tdee * 0.80)
        p_per_kg = 2.2
        f_per_kg = 0.8
    elif "снижение" in g or "похудение" in g:
        kcal = round(tdee * 0.85)
        p_per_kg = 2.0
        f_per_kg = 0.8
    elif "рекомпозиция" in g:
        kcal = round(tdee)
        p_per_kg = 1.9
        f_per_kg = 0.85
    elif "поддержание" in g:
        kcal = round(tdee)
        p_per_kg = 1.2
        f_per_kg = 1.0
    else:
        kcal = round(tdee * 1.12)
        p_per_kg = 1.8
        f_per_kg = 1.1

    protein = round(weight * p_per_kg)
    fat = round(weight * f_per_kg)

    rem_kcal = kcal - (protein * 4 + fat * 9)
    carbs = max(round(rem_kcal / 4), round(weight * 1.5))

    final_kcal = protein * 4 + fat * 9 + carbs * 4

    return {
        "kcal": final_kcal,
        "protein": protein,
        "fat": fat,
        "carbs": carbs
    }
