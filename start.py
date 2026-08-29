import sqlite3
import os

# Инициализираме лека и стабилна база данни без тежки цикли
db_path = "stroy_radar_intel.db"
conn = sqlite3.connect(db_path)
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
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO radar_projects (title, category, location, city, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
              ('Жилищна сграда София Инвест #1', 'ЧСИ Търг', 'София, кв. Лозенец', 'София', 'София Пропърти ООД', '205849120', 'Димитър Георгиев', 150000, 300000, 50.0, 92, 'Активен', '1,200 кв.м', 42.6977, 23.3219))
conn.commit()
conn.close()

# Пускаме Flask приложението
import api_server
