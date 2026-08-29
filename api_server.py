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
                      (f'Инвестиционен обект #{i+1}', 'ЧСИ Търг', 'София, кв. Лозенец', 'София', 'Инвест Груп ООД', '205849120', 'Димитър Георгиев', float(150000 + i*3000), float(300000 + i*6000), 50.0, 92, 'Активен', '1,200 кв.м', 42.6977, 23.3219))
    conn.commit()
    conn.close()

init_db()

FULL_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PRO INVEST RADAR AI .BG – EUR 2026</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { --bg: #080d19; --card-bg: #0d1527; --border: #19253d; --accent-cyan: #00f0ff; --accent-green: #10b981; --accent-yellow: #f59e0b; --accent-blue: #38bdf8; }
        body { background-color: var(--bg); color: #f1f5f9; font-family: sans-serif; padding: 20px; }
        .container-custom { max-width: 1100px; margin: 0 auto; }
        .card-dark { background: var(--card-bg); border: 1px solid var(--border); border-radius: 18px; padding: 20px; margin-bottom: 20px; }
        .custom-input, .custom-select { background: #0f172a !important; border: 1px solid #334155 !important; color: #fff !important; padding: 11px 16px; border-radius: 10px; width: 100%; font-family: monospace; }
        .kpi-card { background: var(--card-bg); border-radius: 16px; padding: 16px; border: 1px solid var(--border); margin-bottom: 15px; }
        .kpi-green  { border-left: 4px solid var(--accent-green) !important; }
        .kpi-blue   { border-left: 4px solid var(--accent-blue) !important; }
        .kpi-yellow { border-left: 4px solid var(--accent-yellow) !important; }
        .kpi-header { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: #64748b; }
        .kpi-value { font-size: 1.85rem; font-weight: 800; color: #fff; margin: 4px 0; }
        #map { height: 400px; width: 100%; border-radius: 14px; border: 1px solid var(--border); }
        .listing-card { background: #0b1120; border: 1px solid var(--border); border-left: 4px solid var(--accent-cyan); border-radius: 14px; padding: 18px; margin-bottom: 16px; }
        .masked-badge { background: #182235; color: #38bdf8; padding: 3px 8px; border-radius: 6px; font-family: monospace; font-size: 0.82rem; border: 1px dashed #0284c7; font-weight: bold; }
        .plan-box { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 14px; cursor: pointer; }
        .plan-popular { border: 2px solid var(--accent-cyan) !important; }
        .btn-plan { background: #1e293b; border: 1px solid #334155; color: #fff; font-weight: 700; padding: 10px 22px; border-radius: 10px; width: 100%; }
        .btn-plan-pro { background: var(--accent-cyan); color: #040810; font-weight: 800; border: none; }
    </style>
</head>
<body>
    <div class="container-custom">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h2 style="color:var(--accent-cyan); font-weight:900; margin-bottom:0;">PRO INVEST RADAR AI .BG</h2>
                <p class="text-secondary small mb-0">Институционален портал за публични търгове, ЧСИ обяви и фирмен одит.</p>
            </div>
            <a href="/export-pdf" target="_blank" class="btn btn-outline-info btn-sm fw-bold">📄 Дневен Бюлетин</a>
        </div>
        
        <!-- ОДИТ СКЕНЕР -->
        <div class="card-dark">
            <h5 class="text-white fw-bold">🔍 ЕИК / БУЛСТАТ Одит</h5>
            <div class="d-flex gap-2 my-2">
                <input type="text" id="eikInput" class="custom-input" value="030431138">
                <button class="btn btn-info fw-bold px-4" onclick="performAudit()">Провери</button>
            </div>
            <div id="auditRes" class="mt-3 p-3 rounded" style="background:#070c18; display:none;">
                <strong class="text-info" id="resName"></strong><br>
                <span class="text-secondary small">Управител: <span class="text-light" id="resMgr"></span></span><br>
                <span class="text-secondary small">Запори: <span class="text-success" id="resInj">НЯМА</span></span>
            </div>
        </div>

        <!-- KPI КАРТИ -->
        <div class="row g-2 mb-3">
            <div class="col-6 col-md-3"><div class="kpi-card"><div class="kpi-header">АКТИВИ</div><div class="kpi-value">{{ stats.total }}</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-green"><div class="kpi-header" style="color:var(--accent-green);">TOP DEALS</div><div class="kpi-value" style="color:var(--accent-green);">{{ stats.top_deals }}</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-blue"><div class="kpi-header" style="color:var(--accent-blue);">ДИСКОНТ</div><div class="kpi-value" style="color:var(--accent-blue);">-{{ stats.avg_discount }}%</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-yellow"><div class="kpi-header" style="color:var(--accent-yellow);">ОБЩ СПРЕД</div><div class="kpi-value" style="color:var(--accent-yellow);">{{ stats.spread_str }} €</div></div></div>
        </div>

        <!-- КАЛКУЛАТОР -->
        <div class="card-dark" style="border-left: 4px solid var(--accent-yellow);">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-warning text-dark fw-bold">🧮 ЧСИ &amp; ТАКСИ КАЛКУЛАТОР 2026</span>
                <span class="text-info fw-bold fs-5" id="calcPriceDisplay">€88 000</span>
            </div>
            <input type="range" min="10000" max="1000000" step="5000" value="88000" class="form-range mb-3" oninput="updateCalculator(this.value)">
            <div class="row g-2 small text-secondary">
                <div class="col-4">Местен данък (3%): <strong class="text-white" id="calcTaxZmdt">€2 640</strong></div>
                <div class="col-4">ЧСИ Такса (1.5%): <strong class="text-white" id="calcTaxChsi">€1 320</strong></div>
                <div class="col-4">Крайна себестойност: <strong class="text-warning" id="calcTotalCost">€92 048</strong></div>
            </div>
        </div>

        <!-- АБОНАМЕНТИ -->
        <div class="row g-3 mb-4">
            <div class="col-md-4"><div class="plan-box h-100"><div class="small fw-bold text-secondary">STARTER EXECUTIVE</div><div class="fw-bold text-white fs-3 my-2">€60 <span class="fs-6 text-secondary">/ мес.</span></div><button class="btn-plan mt-3" onclick="alert('Стартер план')">Избери план</button></div></div>
            <div class="col-md-4"><div class="plan-box plan-popular h-100"><div class="small fw-bold text-info">PRO RISK MONITOR (POPULAR)</div><div class="fw-bold text-white fs-3 my-2">€150 <span class="fs-6 text-secondary">/ мес.</span></div><button class="btn-plan btn-plan-pro mt-3" onclick="alert('PRO план')">ВЗЕМИ PRO</button></div></div>
            <div class="col-md-4"><div class="plan-box h-100"><div class="small fw-bold text-secondary">ENTERPRISE M2M</div><div class="fw-bold text-white fs-3 my-2">€290 <span class="fs-6 text-secondary">/ мес.</span></div><button class="btn-plan mt-3" onclick="alert('Enterprise план')">API Ключ</button></div></div>
        </div>

        <!-- ГИС КАРТА -->
        <div class="card-dark">
            <h5 class="text-white fw-bold mb-3">🗺️ ГИС Карта на обектите</h5>
            <div id="map"></div>
        </div>

        <!-- ОБЯВИ -->
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
                    <div class="fw-bold text-white mb-1">${p[1]}</div>
                    <div class="small text-secondary mb-2">Локация: <span class="masked-badge">${p[3]}</span></div>
                    <div class="text-warning fw-bold">€${Number(p[8]).toLocaleString()} (-${p[10]}%)</div>
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

        function updateCalculator(val) {
            val = Number(val);
            document.getElementById('calcPriceDisplay').innerText = '€' + val.toLocaleString('de-DE');
            document.getElementById('calcTaxZmdt').innerText = '€' + Math.round(val * 0.03).toLocaleString('de-DE');
            document.getElementById('calcTaxChsi').innerText = '€' + Math.round(val * 0.015).toLocaleString('de-DE');
            document.getElementById('calcTotalCost').innerText = '€' + Math.round(val * 1.045).toLocaleString('de-DE');
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

    total = len(projects)
    top_deals = len([p for p in projects if p[11] >= 85])
    avg_disc = round(sum([float(p[10]) for p in projects]) / total, 1) if total else 50.0
    spread = sum([float(p[9]) - float(p[8]) for p in projects])

    stats = {
        "total": total,
        "top_deals": top_deals,
        "avg_discount": str(avg_disc),
        "spread_str": "{:,.0f}".format(spread).replace(",", " ")
    }
    return render_template_string(FULL_HTML, projects_json=json.dumps(projects), stats=stats)

@app.route("/api/audit-eik")
def audit_eik():
    eik = request.args.get("eik", "030431138")
    return jsonify({
        "eik": eik,
        "name": "КОВКО - ВАСИЛЕВ И С-ИЕ СД" if eik == "030431138" else f"Фирма ЕИК {eik}",
        "manager": "Васил Стоянов Василев"
    })

@app.route("/export-pdf")
def export_pdf():
    return "<h3>07:30 ч. Инвестиционен бюлетин</h3>", 200, {'Content-Type': 'text/html; charset=utf-8'}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
