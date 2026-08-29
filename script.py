import csv
from datetime import datetime

raw_feed = [
    {
        "eik": "205849123",
        "company_name": "ТЕХНО СОЛЮШЪНС ЕООД",
        "legal_form": "ЕООД",
        "field_name": "Запор върху дял",
        "event_details": "Наложен запор от ЧСИ Георги Димитров (Рег. № 841) за сума 45,200 лв.",
        "status_date": datetime.today().strftime("%Y-%m-%d"),
        "risk_level": "CRITICAL"
    },
    {
        "eik": "131458992",
        "company_name": "БАЛКАН ЛОГИСТИК ГРУП ООД",
        "legal_form": "ООД",
        "field_name": "Откриване на производство по несъстоятелност",
        "event_details": "Решение на СГС по т.д. 1420/2024. Назначен временен синдик.",
        "status_date": datetime.today().strftime("%Y-%m-%d"),
        "risk_level": "HIGH"
    },
    {
        "eik": "201994821",
        "company_name": "МЕДИКАЛ ДЕНТ БЪЛГАРИЯ АД",
        "legal_form": "АД",
        "field_name": "Смяна на управител / Прехвърляне на дялове",
        "event_details": "Заличаване на предишен управител. Встъпване на ново лице.",
        "status_date": datetime.today().strftime("%Y-%m-%d"),
        "risk_level": "MEDIUM"
    }
]

processed = []
for r in raw_feed:
    category = "Корпоративна промяна"
    if "запор" in r["field_name"].lower():
        category = "Обезпечителна мярка / Запор"
    elif "несъстоятелност" in r["field_name"].lower():
        category = "Фалит / Несъстоятелност"
        
    processed.append({
        "ЕИК": r["eik"],
        "Име на фирма": r["company_name"],
        "Правна форма": r["legal_form"],
        "Категория риск": category,
        "Ниво на опасност": r["risk_level"],
        "Детайли": r["event_details"],
        "Дата": r["status_date"],
        "Линк": f"https://portal.registryagency.bg/CR/Reports/ActiveConditionTabResult?uic={r['eik']}"
    })

filename = f"B2B_Risk_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
with open(filename, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=processed[0].keys())
    writer.writeheader()
    writer.writerows(processed)

print(f"\n[✓] ГОТОВО! Генериран е CSV файл: {filename}\n")
for item in processed:
    print(f"-> {item['ЕИК']} | {item['Име на фирма']} | {item['Ниво на опасност']}")
