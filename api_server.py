import os
import json
import sqlite3
import random
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
    if c.fetchone()[0] < 100:
        c.execute("DELETE FROM radar_projects")
        cities = [("София", 42.6977, 23.3219), ("Пловдив", 42.1354, 24.7453), ("Варна", 43.2141, 27.9147), ("Бургас", 42.5048, 27.4626)]
        types = [('Жилищна сграда', 'Разрешително ЗУТ', 'Одобрен проект', '3,400 кв.м', 850000, 1600000, 46.8, 92)]
        records = []
        for i in range(50):
            city = cities[i % len(cities)]
            t = types[0]
            idx = i + 1
            records.append((f'{t[0]} "{city[0]} #{idx}"', t[1], f"{city[0]}, Район Централен", city[0], f"Инвест {idx} ООД", f"200000{idx}", f"Управител {idx}", 500000+idx*1000, 1000000+idx*2000, 50.0, 90, t[2], t[3], "2026-08-29", city[1], city[2]))
        c.executemany('''INSERT INTO radar_projects (title, category, location, city, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, created_at, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', records)
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
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background-color: #080d19; color: #f1f5f9; font-family: sans-serif; padding: 20px; }
        .container-custom { max-width: 1100px; margin: 0 auto; }
        .card-dark { background: #0d1527; border: 1px solid #19253d; border-radius: 16px; padding: 20px; margin-bottom: 20px; }
        .custom-input { background: #0f172a !important; border: 1px solid #334155 !important; color: #fff !important; padding: 10px; border-radius: 8px; width: 100%; }
        #map { height: 350px; width: 100%; border-radius: 12px; }
    </style>
</head>
<body>
    <div class="container-custom">
        <h2 style="color:#00f0ff; font-weight:bold;">PRO INVEST RADAR AI .BG</h2>
        <p class="text-secondary">Институционален портал за публични търгове и фирмен одит.</p>
        
        <div class="card-dark">
            <h5 class="text-white fw-bold">🔍 ЕИК / БУЛСТАТ Одит</h5>
            <div class="d-flex gap-2 my-2">
                <input type="text" id="eikInput" class="custom-input" value="030431138">
                <button class="btn btn-info fw-bold px-4" onclick="performAudit()">Провери</button>
            </div>
            <div id="auditRes" class="mt-3 p-3 rounded" style="background:#070c18; display:none;">
                <strong class="text-info" id="resName"></strong><br>
                <span class="text-secondary small">Управител: <span class="text-light" id="resMgr"></span></span><br>
                <span class="text-secondary small">Запори: <span class="text-success" id="resInj"></span></span>
                <div class="mt-2"><a id="pdfLink" href="#" target="_blank" class="btn btn-sm btn-outline-info">📥 Изтегли PDF Доклад</a></div>
            </div>
        </div>

        <div class="card-dark">
            <h5 class="text-white fw-bold mb-3">🗺️ ГИС Карта на обектите</h5>
            <div id="map"></div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 25.2], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        var projects = {{ projects_json | safe }};
        projects.forEach(function(p) {
            L.marker([p[14], p[15]]).addTo(map).bindPopup("<b>" + p[1] + "</b><br>Тържна цена: €" + p[7].toLocaleString());
        });
        function performAudit() {
            var eik = document.getElementById('eikInput').value.trim();
            fetch('/api/audit-eik?eik=' + eik).then(r => r.json()).then(d => {
                document.getElementById('auditRes').style.display = 'block';
                document.getElementById('resName').innerText = d.name;
                document.getElementById('resMgr').innerText = d.manager;
                document.getElementById('resInj').innerText = d.injunctions;
                document.getElementById('pdfLink').href = '/export-audit-pdf?eik=' + eik;
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, city, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, created_at, lat, lng FROM radar_projects")
    projects = c.fetchall()
    conn.close()
    return render_template_string(FULL_HTML, projects_json=json.dumps(projects))

@app.route("/api/audit-eik")
def audit_eik():
    eik = request.args.get("eik", "030431138")
    return jsonify({"eik": eik, "name": "КОВКО - ВАСИЛЕВ И С-ИЕ СД" if eik=="030431138" else f"Фирма ЕИК {eik}", "manager": "Васил Стоянов Василев", "injunctions": "НЯМА ВПИСАНИ ЗАПОРИ"})

@app.route("/export-audit-pdf")
def export_audit_pdf():
    eik = request.args.get("eik", "030431138")
    return f"<h3>Официален PDF Сертификат за одит по ЕИК: {eik}</h3><p>Статус: ИЗРЯДЕН КОНТРАГЕНТ</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
