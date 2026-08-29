import sqlite3
import random

DB_PATH = "stroy_radar_intel.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS radar_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    category TEXT,
    location TEXT,
    city TEXT DEFAULT 'София',
    investor TEXT,
    eik TEXT DEFAULT '030431138',
    manager TEXT DEFAULT 'Васил Стоянов Василев',
    price_eur REAL DEFAULT 0,
    market_val REAL DEFAULT 0,
    discount_pct REAL DEFAULT 60.8,
    deal_score INTEGER DEFAULT 88,
    status TEXT DEFAULT 'Активен',
    size_rzp TEXT DEFAULT '4,850 кв.м',
    created_at TEXT DEFAULT '2026-08-29',
    lat REAL DEFAULT 42.6977,
    lng REAL DEFAULT 23.3219
)''')

c.execute("SELECT count(*) FROM radar_projects")
if c.fetchone()[0] < 500:
    c.execute("DELETE FROM radar_projects")
    cities = [
        ("София", 42.6977, 23.3219), ("Пловдив", 42.1354, 24.7453), ("Варна", 43.2141, 27.9147),
        ("Бургас", 42.5048, 27.4626), ("Русе", 43.8563, 25.9700), ("Стара Загора", 42.4258, 25.6345),
        ("Плевен", 43.4170, 24.6067), ("Благоевград", 42.0209, 23.0943), ("Велико Търново", 43.0757, 25.6172),
        ("Добрич", 43.5726, 27.8273), ("Шумен", 43.2712, 26.9361), ("Перник", 42.6052, 23.0378),
        ("Хасково", 41.9344, 25.5556), ("Пазарджик", 42.1928, 24.3336), ("Сливен", 42.6817, 26.3228),
        ("Габрово", 42.8742, 25.3187), ("Враца", 43.2102, 23.5529), ("Видин", 43.9962, 22.8679),
        ("Кърджали", 41.6439, 25.3684), ("Кюстендил", 42.2869, 22.6917), ("Монтана", 43.4085, 23.2257),
        ("Търговище", 43.2512, 26.5721), ("Силистра", 44.1147, 27.2606), ("Ловеч", 43.1370, 24.7142),
        ("Ямбол", 42.4841, 26.5035), ("Разград", 43.5254, 26.5249), ("Смолян", 41.5774, 24.7011),
        ("Банско", 41.8383, 23.4885), ("Несебър", 42.6592, 27.7360), ("Созопол", 42.4170, 27.6953)
    ]
    types = [
        ('Жилищна сграда & апартаменти', 'Разрешително ЗУТ', 'Одобрен проект', '3,400 кв.м', 850000, 1600000, 46.8, 92),
        ('Логистичен склад & терминал', 'ЧСИ Търг', 'Публична продан (II-ри търг)', '8,200 кв.м', 620000, 1450000, 57.2, 89),
        ('Търговска сграда & ритейл площи', 'NPL Дистрес', 'Банково обезпечение', '2,800 кв.м', 490000, 1100000, 55.4, 87),
        ('Производствена база & цех', 'НАП Публична продан', 'Данъчен търг', '5,100 кв.м', 380000, 890000, 57.3, 85),
        ('Офис сграда с подземен паркинг', 'Разрешително ЗУТ', 'Разрешение в сила', '4,900 кв.м', 1250000, 2400000, 47.9, 90)
    ]
    records = []
    for i in range(1000):
        city = cities[i % len(cities)]
        t = types[i % len(types)]
        idx = i + 1
        title = f'{t[0]} "{city[0]} Инвест #{idx}"'
        location = f"{city[0]}, Район Индустриален / Жилищен кв. {idx % 15 + 1}"
        investor = f"{city[0]} Пропърти Груп {idx} ООД"
        eik = str(200000000 + idx * 13)
        manager = f"Инж. {city[0]}ски {idx}"
        lat = city[1] + random.uniform(-0.06, 0.06)
        lng = city[2] + random.uniform(-0.06, 0.06)
        price = t[4] + (idx * 350) % 400000
        mval = t[5] + (idx * 750) % 800000
        disc = round(((mval - price) / mval) * 100, 1)
        score = min(99, max(75, int(t[7] + (idx % 8) - 3)))
        c_date = "2026-08-29" if (idx % 5 == 0) else "2026-08-28"
        records.append((title, t[1], location, city[0], investor, eik, manager, price, mval, disc, score, t[2], t[3], c_date, lat, lng))
        
    c.executemany('''INSERT INTO radar_projects 
        (title, category, location, city, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, created_at, lat, lng)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', records)
conn.commit()
conn.close()
print("Database initialized successfully.")
