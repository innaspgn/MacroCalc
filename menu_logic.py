import random

def filter_dishes(dishes: list, category: str, filters: dict) -> list:
    result = []
    max_time = filters.get("max_time", "Не важно")
    
    for d in dishes:
        if d.get("category") != category:
            continue
            
        # Фильтр по времени готовки
        if max_time != "Не важно":
            if d.get("cook_time", 15) > int(max_time):
                continue
                
        # Фильтр завтраков
        if category == "Завтрак":
            b_type = filters.get("breakfast_type", "Оба")
            if b_type != "Оба" and d.get("sub_type") != b_type:
                continue
                
        # Фильтр белка для обеда и ужина
        if category in ["Обед", "Ужин"]:
            p_type = filters.get("protein_type", "Любой")
            if p_type != "Любой" and d.get("protein_type") not in [p_type, "Без мяса/рыбы"]:
                continue
                
        # Фильтр десертов
        if category == "Десерт":
            d_type = filters.get("dessert_type", "Любые")
            if d_type != "Любые" and d.get("sub_type") != d_type:
                continue
                
        # Фильтр перекусов (магазинные ON/OFF)
        if category == "Перекус":
            if not filters.get("allow_store_snacks", True) and d.get("is_store_bought", False):
                continue
                
        result.append(d)
    return result


def build_ration_plan(dishes: list, targets: dict, existing_entries: list, mode: str, filters: dict) -> list:
    """
    Собирает рацион либо с нуля ('all'), либо добавляя недостающие приемы ('missing').
    Автоматически подгоняет граммовку блюд под оставшиеся калории.
    """
    base_entries = [] if mode == "all" else [e.copy() for e in existing_entries]
    existing_meals = {e["meal"] for e in base_entries}
    
    used_kcal = sum(e["kcal"] for e in base_entries)
    rem_kcal = max(targets["kcal"] - used_kcal, 0)
    
    if rem_kcal < 80:
        return base_entries

    # Определяем, какие приемы пищи нужно заполнить
    plan_slots = []
    if mode == "all" or "Завтрак" not in existing_meals:
        plan_slots.append(("Завтрак", 0.25))
    if mode == "all" or "Обед" not in existing_meals:
        plan_slots.append(("Обед", 0.35))
    if mode == "all" or "Ужин" not in existing_meals:
        plan_slots.append(("Ужин", 0.25))
        
    # Перекус или десерт на остаток калорий
    if mode == "all" or ("Перекус" not in existing_meals and "Десерт" not in existing_meals):
        has_desserts = len(filter_dishes(dishes, "Десерт", filters)) > 0
        slot_cat = "Десерт" if (has_desserts and random.choice([True, False])) else "Перекус"
        plan_slots.append((slot_cat, 0.15))

    if not plan_slots:
        return base_entries

    total_weight = sum(w for _, w in plan_slots)
    new_entries = []

    for cat, weight in plan_slots:
        candidates = filter_dishes(dishes, cat, filters)
        # Если по строгим фильтрам пусто, пробуем взять любое блюдо этой категории
        if not candidates:
            candidates = [d for d in dishes if d.get("category") == cat]
        if not candidates:
            continue
            
        chosen = random.choice(candidates)
        slot_kcal = rem_kcal * (weight / total_weight)
        
        if chosen["kcal"] > 0:
            # Округляем граммовку до 5 г для удобства взвешивания
            grams = max(round((slot_kcal / chosen["kcal"]) * 100 / 5) * 5, 30)
            factor = grams / 100
            new_entries.append({
                "meal": cat,
                "name": chosen["name"],
                "grams": grams,
                "kcal": round(chosen["kcal"] * factor),
                "protein": round(chosen["protein"] * factor, 1),
                "fat": round(chosen["fat"] * factor, 1),
                "carbs": round(chosen["carbs"] * factor, 1)
            })

    return base_entries + new_entries
