import os
import json
import sqlite3
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
    if c.fetchone()[0] < 20:
        c.execute("DELETE FROM radar_projects")
        for i in range(20):
            c.execute("INSERT INTO radar_projects (title, category, location, city, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (f'Инвестиционен обект #{i+1}', 'ЧСИ Търг', 'София, кв. Лозенец', 'София', 'Инвест Груп ООД', '205849120', 'Димитър Георгиев', 150000.0 + i*3000.0, 300000.0 + i*6000.0, 50.0, 92, 'Активен', '1,200 кв.м', 42.6977, 23.3219))
    conn.commit()
    conn.close()

init_db()

FULL_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PRO INVEST RADAR AI .BG</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background-color: #080d19; color: #f1f5f9; font-family: sans-serif; padding: 20px; }
        .card-dark { background: #0d1527; border: 1px solid #19253d; border-radius: 16px; padding: 20px; margin-bottom: 20px; }
        .custom-input { background: #0f172a !important; border: 1px solid #334155 !important; color: #fff !important; padding: 10px; border-radius: 8px; width: 100%; }
        #map { height: 350px; width: 100%; border-radius: 12px; }
        .listing-card { background: #0b1120; border: 1px solid #19253d; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container" style="max-width: 1000px;">
        <h2 style="color: #00f0ff; font-weight: bold;">PRO INVEST RADAR AI .BG</h2>
        <p class="text-secondary">Институционален портал за публични търгове и фирмен одит.</p>
        
        <div class="card-dark">
            <h5 class="text-white fw-bold">🔍 ЕИК / БУЛСТАТ Одит</h5>
            <div class="d-flex gap-2 my-2">
                <input type="text" id="eikInput" class="custom-input" value="030431138">
                <button class="btn btn-info fw-bold px-4" onclick="performAudit()">Провери</button>
            </div>
            <div id="auditRes" class="mt-3 p-3 rounded" style="background:#070c18; display:none;">
                <strong class="text-info" id="resName"></strong><br>
                <span class="text-secondary small">Управител: <span class="text-light" id="resMgr"></span></span>
            </div>
        </div>

        <div class="card-dark">
            <h5 class="text-white fw-bold mb-3">🗺️ ГИС Карта на обектите</h5>
            <div id="map"></div>
        </div>

        <div class="card-dark">
            <h5 class="text-white fw-bold mb-3">📋 Активни обяви в системата</h5>
            <div class="row" id="dealsContainer"></div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 23.3219], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        var projects = JSON.parse('{{ projects_json | safe }}');
        var container = document.getElementById('dealsContainer');
        
        projects.forEach(function(p) {
            L.marker([p[15], p[16]]).addTo(map).bindPopup("<b>" + p[1] + "</b><br>Цена: €" + Number(p[8]).toLocaleString());
            
            var col = document.createElement('div');
            col.className = 'col-md-6';
            col.innerHTML = `
                <div class="listing-card">
                    <div class="fw-bold text-white">${p[1]}</div>
                    <div class="small text-secondary">Локация: ${p[3]}</div>
                    <div class="text-warning fw-bold mt-2">€${Number(p[8]).toLocaleString()}</div>
                </div>
            `;
            container.appendChild(col);
        });

        function performAudit() {
            var eik = document.getElementById('eikInput').value.trim();
            fetch('/api/audit-eik?eik=' + eik).then(r => r.json()).then(d => {
                document.getElementById('auditRes').style.display = 'block';
                document.getElementById('resName').innerText = d.name;
                document.getElementById('resMgr').innerText = d.manager;
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
    return jsonify({
        "eik": eik,
        "name": "КОВКО - ВАСИЛЕВ И С-ИЕ СД" if eik == "030431138" else f"Фирма ЕИК {eik}",
        "manager": "Васил Стоянов Василев"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
