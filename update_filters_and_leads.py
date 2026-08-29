import sqlite3

DB_PATH = "stroy_radar_intel.db"

# Списък с големи строителни компании, инвеститори и търговци
new_b2b_targets = [
    ("office@pipeline.bg", "Пайплайн ООД"),
    ("office@gbs-sofia.com", "ГБС София"),
    ("sales@comforteood.com", "Комфорт ООД"),
    ("office@argogroup-exact.com", "Аргогруп Екзакт"),
    ("office@blagovest.bg", "Благовест Строителство"),
    ("office@monolit.bg", "Монолит София"),
    ("office@kristian-neiko.com", "Кристиан Нейко"),
    ("office@bulgarstroy.bg", "Булгарстрой АД"),
    ("info@sofia-invest.bg", "София Инвест Груп"),
    ("office@eurobuilding.bg", "Евробилдинг Инженеринг"),
    ("contact@termostroy.bg", "Термострой ЕООД"),
    ("info@varna-build.com", "Варна Билд Корп"),
    ("office@plovdiv-stroy.bg", "Пловдив Строй Инвест"),
    ("office@burgas-invest.com", "Бургас Инвест Строй"),
    ("sales@beton-el.bg", "Бетон Ел Трейд"),
    ("office@armatur-stroy.bg", "Арматурни Заготовки ООД"),
    ("info@hydroizolacii.bg", "Хидроизолации Инженеринг"),
    ("office@metal-construct.bg", "Метал Конструкт"),
    ("contact@fasadi-build.bg", "Фасадни Системи ООД"),
    ("office@el-instalacii.bg", "Електро Системи Инженеринг")
]

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 1. Добавяне на таблица с разширени филтри
c.execute('''
    CREATE TABLE IF NOT EXISTS project_filters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filter_name TEXT,
        category TEXT,
        min_value REAL,
        max_value REAL,
        region TEXT
    )
''')

# 2. Добавяне на стандартни филтърни правила
default_filters = [
    ("Жилищни сгради над 1000 кв.м", "residential", 1000.0, 0, "София"),
    ("ЧСИ парцели под пазарна цена", "csi_land", 0, 500000.0, "Всички"),
    ("Промишлени складове и бази", "industrial", 500.0, 0, "Пловдив"),
    ("Нови разрешителни за строеж", "permits", 0, 0, "Всички")
]

for name, cat, min_v, max_v, reg in default_filters:
    c.execute("INSERT OR IGNORE INTO project_filters (filter_name, category, min_value, max_value, region) VALUES (?, ?, ?, ?, ?)",
              (name, cat, min_v, max_v, reg))

# 3. Вкарване на новите таргетирани B2B лидове
added = 0
for email, name in new_b2b_targets:
    try:
        c.execute("INSERT OR IGNORE INTO leads_outreach (email, company_name, status) VALUES (?, ?, 'pending')", (email, name))
        added += 1
    except Exception:
        pass

conn.commit()
conn.close()
print(f"[✓] Успешно обновени филтри и заредени {added} нови фирмени контакта за B2B кампании!")
