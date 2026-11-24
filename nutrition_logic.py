ACTIVITY_MULTIPLIERS = {
    "Сидячая работа, минимум движения и тренировок": 1.2,
    "Легкая активность (1–3 легкие тренировки в неделю или прогулки)": 1.375,
    "Средняя активность (3–5 тренировок средней интенсивности в неделю)": 1.55,
    "Высокая активность (интенсивные тренировки 5–7 раз в неделю или физический труд)": 1.725
}

def calculate_bmi(weight_kg: float, height_cm: float) -> tuple[float, str]:
    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)
    if bmi < 18.5:
        status = "Дефицит массы тела"
    elif bmi < 25:
        status = "Норма"
    elif bmi < 30:
        status = "Избыточная масса тела"
    else:
        status = "Ожирение"
    return bmi, status

def calculate_targets(profile: dict) -> dict:
    weight = profile["weight"]
    height = profile["height"]
    age = profile["age"]
    gender = profile.get("gender", "Женский")
    activity_str = profile.get("activity", "")
    act_mult = ACTIVITY_MULTIPLIERS.get(activity_str, 1.375)
    goal = profile.get("goal", "Рекомпозиция")
    
    if gender == "Мужской":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        
    tdee = bmr * act_mult
    
    if goal == "Сушка":
        target_kcal = tdee * 0.85
        p_per_kg = 1.7
        f_per_kg = 0.8
    elif goal == "Набор":
        target_kcal = tdee * 1.125
        p_per_kg = 1.9
        f_per_kg = 1.1
    else:
        target_kcal = tdee
        f_per_kg = 0.95
        if act_mult <= 1.2:
            p_per_kg = 1.0
        elif act_mult <= 1.375:
            p_per_kg = 1.35
        else:
            p_per_kg = 1.7

    hormones = profile.get("hormones", "Нет особенностей")
    if hormones == "Гипотиреоз":
        target_kcal *= 0.95
    elif hormones == "Инсулинорезистентность / СПКЯ":
        p_per_kg = min(p_per_kg + 0.15, 2.2)

    protein_g = round(weight * p_per_kg)
    fat_g = max(round(weight * f_per_kg), 45)
    
    protein_kcal = protein_g * 4
    fat_kcal = fat_g * 9
    
    raw_carbs_g = round((target_kcal - protein_kcal - fat_kcal) / 4)
    carbs_g = max(raw_carbs_g, 115)
    
    final_kcal = (protein_g * 4) + (fat_g * 9) + (carbs_g * 4)
    
    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "kcal": final_kcal,
        "protein": protein_g,
        "fat": fat_g,
        "carbs": carbs_g
    }
