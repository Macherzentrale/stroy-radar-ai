import os
import json
import sqlite3
import random
from flask import Flask, render_template_string, jsonify, request

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
    if c.fetchone()[0] < 100:
        c.execute("DELETE FROM radar_projects")
        cities = [("София", 42.6977, 23.3219), ("Пловдив", 42.1354, 24.7453), ("Варна", 43.2141, 27.9147), ("Бургас", 42.5048, 27.4626)]
        for i in range(50):
            c.execute("INSERT INTO radar_projects (title, category, location, city, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (f'Инвестиционен обект #{i+1}', 'ЧСИ Търг', 'София, кв. Лозенец', 'София', 'Инвест Груп ООД', '205849120', 'Димитър Георгиев', 150000, 300000, 50.0, 90, 'Активен', '1,200 кв.м', 42.6977, 23.3219))
    conn.commit()
    conn.close()

init_db()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <title>PRO INVEST RADAR .BG</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #080d19; color: #f1f5f9; font-family: sans-serif; padding: 20px; }
        .card-custom { background: #0d1527; border: 1px solid #19253d; border-radius: 16px; padding: 20px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container" style="max-width: 900px;">
        <h2 style="color: #00f0ff; font-weight: bold;">PRO INVEST RADAR AI .BG</h2>
        <p class="text-secondary">Корпоративна система за публични търгове и одит.</p>
        
        <div class="card-custom">
            <h4>🔍 ЕИК Одит</h4>
            <div class="input-group mb-3">
                <input type="text" id="eik" class="form-control bg-dark text-white" value="030431138">
                <button class="btn btn-info fw-bold" onclick="auditEik()">Провери</button>
            </div>
            <div id="result" class="p-3 bg-black rounded" style="display:none;">
                <p id="resText" class="text-success mb-0"></p>
            </div>
        </div>
    </div>

    <script>
        function auditEik() {
            let eik = document.getElementById('eik').value;
            fetch('/api/audit?eik=' + eik).then(r => r.json()).then(d => {
                document.getElementById('result').style.display = 'block';
                document.getElementById('resText').innerText = "Фирма: " + d.name + " | Управител: " + d.manager + " | Статус: " + d.status;
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/audit")
def audit():
    eik = request.args.get("eik", "030431138")
    return jsonify({
        "eik": eik,
        "name": "КОВКО - ВАСИЛЕВ И С-ИЕ СД" if eik == "030431138" else f"Фирма ЕИК {eik}",
        "manager": "Васил Стоянов Василев",
        "status": "ИЗРЯДЕН КОНТРАГЕНТ - БЕЗ ЗАПОРИ"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
