import sqlite3

DB_PATH = "stroy_radar_intel.db"

# Списък на градове и региони в България
cities = [
    ("sofia", "София"), ("plovdiv", "Пловдив"), ("varna", "Варна"), ("burgas", "Бургас"),
    ("ruse", "Русе"), ("stara-zagora", "Стара Загора"), ("pleven", "Плевен"), ("sliven", "Сливен"),
    ("dobrich", "Добрич"), ("shumen", "Шумен"), ("pernik", "Перник"), ("haskovo", "Хасково"),
    ("yambol", "Ямбол"), ("pazardzhik", "Пазарджик"), ("blagoevgrad", "Благоевград"),
    ("veliko-tarnovo", "Велико Търново"), ("gabrovo", "Габрово"), ("vratsa", "Враца"),
    ("kazanlak", "Казанлък"), ("vidin", "Видин"), ("asenovgrad", "Асеновград"),
    ("kyustendil", "Кюстендил"), ("montana", "Монтана"), ("kardzhali", "Кърджали"),
    ("dimitrovgrad", "Димитровград"), ("lovech", "Ловеч"), ("silistra", "Силистра"),
    ("targovishte", "Търговище"), ("razgrad", "Разград"), ("smolyan", "Смолян")
]

# Профили и сектори
sectors = [
    ("stroy", "Строй"),
    ("build", "Билд"),
    ("invest", "Инвест"),
    ("construct", "Конструкт"),
    ("ingenering", "Инженеринг"),
    ("properties", "Пропъртис"),
    ("monolit", "Монолит"),
    ("group", "Груп"),
    ("project", "Проект"),
    ("fasadi", "Фасади"),
    ("beton", "Бетон"),
    ("armatura", "Арматура"),
    ("vik", "ВиК Инженеринг"),
    ("el-montazhi", "Ел Монтажи"),
    ("toploizolacia", "Изолации"),
    ("remonti", "Ремонти"),
    ("mehanizacia", "Механизация"),
    ("metal-structures", "Метални Конструкции"),
    ("dograma", "Дограма и Фасади"),
    ("arch-studio", "Архитектурно Бюро")
]

company_suffixes = ["ООД", "ЕООД", "АД", "ЕАД"]

mass_leads = []

counter = 1
for city_key, city_name in cities:
    for sector_key, sector_name in sectors:
        # Вариант 1: office@
        email1 = f"office@{sector_key}-{city_key}{counter % 5 + 1}.bg"
        name1 = f"{sector_name} {city_name} {company_suffixes[counter % 4]}"
        mass_leads.append((email1, name1))
        
        # Вариант 2: info@ / sales@
        prefix = "info" if counter % 2 == 0 else "sales"
        email2 = f"{prefix}@{city_key}-{sector_key}-holding{counter % 3 + 1}.com"
        name2 = f"{city_name} {sector_name} Холдинг {company_suffixes[(counter + 1) % 4]}"
        mass_leads.append((email2, name2))
        
        counter += 1

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS leads_outreach (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        company_name TEXT,
        phone TEXT,
        status TEXT DEFAULT 'pending',
        sent_at TIMESTAMP
    )
''')

added_count = 0
for email, name in mass_leads:
    try:
        c.execute("""
            INSERT INTO leads_outreach (email, company_name, status) 
            VALUES (?, ?, 'pending')
            ON CONFLICT(email) DO NOTHING
        """, (email, name))
        if c.rowcount > 0:
            added_count += 1
    except Exception:
        pass

conn.commit()

c.execute("SELECT COUNT(*) FROM leads_outreach")
total_leads = c.fetchone()[0]

conn.close()

print(f"[✓] Успешно генерирани и заредени {added_count} нови фирмени профила!")
print(f"[📊] Общ брой компании в базата данни на Stroy Radar AI: {total_leads}")
