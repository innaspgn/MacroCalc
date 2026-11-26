ACTIVITY_MULTIPLIERS = {
    "Минимальная (сидячий образ жизни, нет тренировок)": 1.2,
    "Низкая (1–2 легкие тренировки в неделю)": 1.375,
    "Средняя (3–4 тренировки в неделю)": 1.55,
    "Высокая (5–6 интенсивных тренировок в неделю)": 1.725,
    "Экстремальная (ежедневные тренировки / физический труд)": 1.9
}

GOAL_LIST = [
    "Похудение",
    "Рекомпозиция (снижение жира + рост мышц)",
    "Поддержание веса",
    "Набор массы"
]

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

def calculate_targets(gender: str, age: int, height: float, weight: float, activity: str, goal: str) -> dict:
    # Формула Миффлина — Сан-Жеора
    if gender == "Женский":
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5

    mult = ACTIVITY_MULTIPLIERS.get(activity, 1.375)
    tdee = bmr * mult

    if goal == "Похудение":
        kcal = round(tdee * 0.85)
        p_per_kg = 2.0
        f_per_kg = 0.8
    elif "Рекомпозиция" in goal:
        kcal = round(tdee)
        p_per_kg = 1.9
        f_per_kg = 0.85
    elif "Поддержание" in goal:
        kcal = round(tdee)
        p_per_kg = 1.2
        f_per_kg = 1.0
    else:  # Набор массы
        kcal = round(tdee * 1.12)
        p_per_kg = 1.8
        f_per_kg = 1.1

    protein = round(weight * p_per_kg)
    fat = round(weight * f_per_kg)

    # Оставшиеся калории направляем на углеводы (минимум 1.5 г/кг)
    rem_kcal = kcal - (protein * 4 + fat * 9)
    carbs = max(round(rem_kcal / 4), round(weight * 1.5))

    # Итоговую калорийность синхронизируем с суммой БЖУ
    final_kcal = protein * 4 + fat * 9 + carbs * 4

    return {
        "kcal": final_kcal,
        "protein": protein,
        "fat": fat,
        "carbs": carbs
    }
