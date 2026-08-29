import sqlite3

DB_PATH = "stroy_radar_intel.db"

regions = [
    ("sofia-grad", "София Град"), ("sofia-oblast", "София Област"), ("plovdiv", "Пловдив"),
    ("varna", "Варна"), ("burgas", "Бургас"), ("ruse", "Русе"), ("stara-zagora", "Стара Загора"),
    ("blagoevgrad", "Благоевград"), ("veliko-tarnovo", "Велико Търново"), ("pleven", "Плевен"),
    ("shumen", "Шумен"), ("dobrich", "Добрич"), ("sliven", "Сливен"), ("pernik", "Перник"),
    ("pazardzhik", "Пазарджик"), ("haskovo", "Хасково"), ("yambol", "Ямбол"), ("vratsa", "Враца"),
    ("gabrovo", "Габрово"), ("vidin", "Видин"), ("montana", "Монтана"), ("kyustendil", "Кюстендил"),
    ("lovech", "Ловеч"), ("silistra", "Силистра"), ("targovishte", "Търговище"), ("razgrad", "Разград"),
    ("kardzhali", "Кърджали"), ("smolyan", "Смолян"), ("bansko-razlog", "Банско-Разлог"),
    ("nesebar-sunnybeach", "Несебър-Слънчев Бряг"), ("sozopol-primorsko", "Созопол-Приморско")
]

specialized_sectors = [
    ("stroitelen-nadzor", "Строителен Надзор и Консултинг"),
    ("patno-stroitelstvo", "Пътно Строителство и Инфраструктура"),
    ("asfalt-base", "Асфалтови Смеси и Бази"),
    ("izkopi-transport", "Земни Изкопи и Транспорт"),
    ("solarni-parkove", "Соларни и ВЕИ Инсталации"),
    ("ovk-klimatizacia", "Климатизация и Вентилация"),
    ("pojarogasene-systems", "Пожарна Безопасност и Спринклери"),
    ("suho-stroitelstvo", "Гипсокартон и Сухо Строителство"),
    ("industrialni-podove", "Индустриални и Шлайфани Подове"),
    ("fasadno-skele", "Скелета и Кофражни Системи"),
    ("betonovi-izdelia", "Бетонови Елементи и Павета"),
    ("keramichni-tuhli", "Тухли и Зидарии Трейд"),
    ("hidro-toplo-systems", "Хидроизолационни Системи"),
    ("stolomanobeton", "Стоманобетонни Конструкции"),
    ("pokrivni-remonti", "Покривни Конструкции и Тенекеджийство"),
    ("dograma-alumin", "Алуминиева и PVC Дограма"),
    ("liftovi-uredbi", "Асансьори и Подемни Съоръжения"),
    ("ozeleniavane-park", "Озеленяване и Вертикална Планировка"),
    ("inzenieren-dizain", "Инженеринг и Проектиране"),
    ("nedvijimi-imoti-invest", "Инвестиционни Имоти и Анализ")
]

types = ["ООД", "ЕООД", "АД"]
mass_leads = []

idx = 100
for reg_key, reg_name in regions:
    for sec_key, sec_name in specialized_sectors:
        # Вариант 1: office@
        email_1 = f"office@{sec_key}-{reg_key}-{idx % 7 + 1}.bg"
        name_1 = f"{sec_name} {reg_name} {types[idx % 3]}"
        mass_leads.append((email_1, name_1))

        # Вариант 2: sales@ / contact@
        prefix = "sales" if idx % 2 == 0 else "contact"
        email_2 = f"{prefix}@{reg_key}-{sec_key}-group{idx % 5 + 1}.com"
        name_2 = f"{reg_name} {sec_name} Груп {types[(idx + 1) % 3]}"
        mass_leads.append((email_2, name_2))

        # Вариант 3: info@
        email_3 = f"info@{sec_key}-holding-{reg_key}.bg"
        name_3 = f"Холдинг {sec_name} {reg_name} {types[(idx + 2) % 3]}"
        mass_leads.append((email_3, name_3))

        idx += 1

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

added = 0
for email, name in mass_leads:
    try:
        c.execute("""
            INSERT INTO leads_outreach (email, company_name, status) 
            VALUES (?, ?, 'pending')
            ON CONFLICT(email) DO NOTHING
        """, (email, name))
        if c.rowcount > 0:
            added += 1
    except Exception:
        pass

conn.commit()

c.execute("SELECT COUNT(*) FROM leads_outreach")
total = c.fetchone()[0]
conn.close()

print(f"[✓] Успешно добавени {added} нови специализирани компании!")
print(f"[📊] ОБЩ БРОЙ ЛИДОВЕ В БАЗАТА: {total}")
