import json
import csv
from datetime import datetime

def calculate_deal_score(item):
    """
    Алгоритъм за оценка на инвестиционната изгода и риск профила.
    """
    price = item.get("Стойност (число)", 0.0)
    title = item.get("Имот / Описание", "").lower()
    
    score = 50  # Базов скор
    flags = []
    
    # Фактор 1: Тип на имота
    if "апартамент" in title or "жилище" in title:
        score += 25
        flags.append("Висока ликвидност (жилищен фонд)")
    elif "склад" in title or "производствен" in title:
        score += 15
        flags.append("Индустриален капацитет")
    elif "магазин" in title or "търговски" in title:
        score += 10
        flags.append("Търговска площ")

    # Фактор 2: Ценова категория
    if 0 < price <= 150000:
        score += 20
        flags.append("Достъпен праг за бърза препродажба")
    elif price > 500000:
        score -= 10
        flags.append("Висока капиталова експозиция")
        
    score = max(min(score, 100), 0)
    
    # Категоризация
    if score >= 80:
        rating = "TOP DEAL / СИЛНО ИЗГОДНО"
    elif score >= 60:
        rating = "GOOD OPPORTUNITY / СТАНДАРТЕН ИНТЕРЕС"
    else:
        rating = "HIGH RISK / СПЕЦИФИЧЕН АКТИВ"
        
    return score, rating, " | ".join(flags)

def process_and_enrich():
    print("[*] Стартиране на AI Скоринг Модула...")
    
    # Зареждане на последните сурови данни
    items = [
        {
            "Имот / Описание": "Двустаен апартамент 68.50 кв.м, ет. 4",
            "Начална цена": "112 500.00 лв.",
            "Стойност (число)": 112500.0,
            "Краен срок": "15.09.2026",
            "Линк към търга": "https://sales.bcpea.org/properties/104921"
        },
        {
            "Имот / Описание": "Производствен склад и парцел 420 кв.м",
            "Начална цена": "240 000.00 лв.",
            "Стойност (число)": 240000.0,
            "Краен срок": "22.09.2026",
            "Линк към търга": "https://sales.bcpea.org/properties/104922"
        },
        {
            "Имот / Описание": "Търговски обект / Магазин 95.00 кв.м",
            "Начална цена": "89 000.00 лв.",
            "Стойност (число)": 89000.0,
            "Краен срок": "30.09.2026",
            "Линк към търга": "https://sales.bcpea.org/properties/104923"
        }
    ]
    
    enriched_data = []
    llms_text_lines = [
        "# РАФИНИРАН ФИЙД: АКТУАЛНИ ЧСИ ТЪРГОВЕ И ОЦЕНКА НА РИСКА",
        f"# Последна актуализация: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "---"
    ]
    
    for itm in items:
        score, rating, rationale = calculate_deal_score(itm)
        
        enriched_item = {
            **itm,
            "AI_Скор": score,
            "AI_Рейтинг": rating,
            "AI_Анализ": rationale
        }
        enriched_data.append(enriched_item)
        
        # Подготовка за LLMs.txt
        llms_text_lines.append(f"## Имот: {itm['Имот / Описание']}")
        llms_text_lines.append(f"- Начална цена: {itm['Начална цена']}")
        llms_text_lines.append(f"- AI Инвестиционен скор: {score}/100 ({rating})")
        llms_text_lines.append(f"- Ключови фактори: {rationale}")
        llms_text_lines.append(f"- Линк: {itm['Линк към търга']}\n")

    # 1. Запис в JSON (За API ендпойнти и софтуер)
    json_filename = "ai_enriched_market_feed.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, ensure_ascii=False, indent=2)
        
    # 2. Запис в LLMs.txt (За Claude, ChatGPT и Web Agents)
    llms_filename = "llms.txt"
    with open(llms_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(llms_text_lines))
        
    print(f"\n[✓] AI Скорингът завърши успешно!")
    print(f"[✓] Генериран JSON за машини/API: {json_filename}")
    print(f"[✓] Генериран LLMs.txt за AI Агенти: {llms_filename}")
    
    print("\n--- РЕЗУЛТАТИ ОТ AI АНАЛИЗА ---")
    for res in enriched_data:
        print(f"[{res['AI_Скор']}/100] {res['Имот / Описание']} -> {res['AI_Рейтинг']}")

if __name__ == "__main__":
    process_and_enrich()
