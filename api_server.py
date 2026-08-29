import os
import json
import sqlite3
from flask import Flask, render_template_string, jsonify, Response, request

app = Flask(__name__)
DB_PATH = "stroy_radar_intel.db"

def init_db():
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
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO radar_projects (title, category, location, city, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, lat, lng) VALUES ('Многофамилна жилищна сграда Елит Резидънс', 'Разрешително ЗУТ', 'София, кв. Лозенец', 'София', 'Елит Строй ООД', '205849120', 'Димитър Георгиев', 1850000, 3200000, 42.1, 94, 'Активен', '4,850 кв.м', 42.6622, 23.3185)")
    conn.commit()
    conn.close()

init_db()

FULL_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PRO INVEST RADAR .BG</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #080d19; color: #f1f5f9; font-family: sans-serif; padding: 20px; text-align: center; }
        .box { max-width: 600px; margin: 50px auto; background: #0d1527; border: 1px solid #19253d; padding: 30px; border-radius: 16px; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color:#00f0ff; font-weight:bold;">PRO INVEST RADAR .BG</h2>
        <p class="text-secondary mt-3">Системата работи успешно в реално време.</p>
        <a href="/api/deals" class="btn btn-info mt-2 fw-bold">JSON API Статус</a>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(FULL_HTML)

@app.route("/api/deals")
def api_deals():
    return jsonify({"status": "active", "server": "online"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
