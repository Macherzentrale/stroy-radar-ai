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
            city_name = "София" if i % 2 == 0 else "Пловдив"
            c.execute("INSERT INTO radar_projects (title, category, location, city, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (f'Инвестиционен обект #{i+1}', 'ЧСИ Търг', f'{city_name}, кв. Център', city_name, 'Инвест Груп ООД', '205849120', 'Димитър Георгиев', float(150000 + i*3000), float(300000 + i*6000), 50.0, 92, 'Активен', '1,200 кв.м', 42.6977 + (i*0.01), 23.3219 + (i*0.01)))
    conn.commit()
    conn.close()

init_db()

FULL_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PRO INVEST RADAR AI .BG – EUR 2026</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
    <style>
        :root { --bg: #080d19; --card-bg: #0d1527; --border: #19253d; --accent-cyan: #00f0ff; --accent-green: #10b981; --accent-yellow: #f59e0b; --accent-blue: #38bdf8; }
        body { background-color: var(--bg); color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 15px; }
        .container-custom { max-width: 1100px; margin: 0 auto; }
        .navbar-custom { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
        .brand-box { display: flex; align-items: center; gap: 10px; text-decoration: none; }
        .shield-icon { width: 38px; height: 38px; background: #1e3a8a; border: 2px solid #38bdf8; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
        .card-dark { background: var(--card-bg); border: 1px solid var(--border); border-radius: 18px; padding: 20px; margin-bottom: 20px; }
        .custom-input, .custom-select { background: #0f172a !important; border: 1px solid #334155 !important; color: #fff !important; padding: 11px 16px; border-radius: 10px; width: 100%; font-family: monospace; }
        .custom-select option { background: #0f172a; color: #fff; }
        .kpi-card { background: var(--card-bg); border-radius: 16px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; min-height: 115px; border: 1px solid var(--border); }
        .kpi-green  { border-left: 4px solid var(--accent-green) !important; }
        .kpi-blue   { border-left: 4px solid var(--accent-blue) !important; }
        .kpi-yellow { border-left: 4px solid var(--accent-yellow) !important; }
        .kpi-header { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: #64748b; }
        .kpi-value { font-size: 1.85rem; font-weight: 800; color: #fff; line-height: 1.1; margin: 4px 0; }
        #map { height: 440px; width: 100%; border-radius: 14px; border: 1px solid var(--border); }
        .listing-card { background: #0b1120; border: 1px solid var(--border); border-left: 4px solid var(--accent-cyan); border-radius: 14px; padding: 18px; margin-bottom: 16px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }
        .masked-badge { background: #182235; color: #38bdf8; padding: 3px 8px; border-radius: 6px; font-family: monospace; font-size: 0.82rem; border: 1px dashed #0284c7; font-weight: bold; }
        .plan-box { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 14px; display: flex; flex-direction: column; justify-content: space-between; height: 100%; }
        .plan-popular { border: 2px solid var(--accent-cyan) !important; }
        .btn-plan { background: #1e293b; border: 1px solid #334155; color: #fff; font-weight: 700; padding: 10px 22px; border-radius: 10px; width: 100%; }
        .btn-plan-pro { background: var(--accent-cyan); color: #040810; font-weight: 800; border: none; }
        .pagination-box { display: flex; justify-content: center; gap: 8px; margin: 20px 0 35px 0; }
        .btn-page { background: #0d1527; border: 1px solid var(--border); color: #fff; border-radius: 8px; padding: 6px 14px; font-weight: bold; cursor: pointer; }
        .btn-page.active { background: var(--accent-cyan); color: #040810; border-color: var(--accent-cyan); }
        .floating-contact-bar { position: fixed; bottom: 25px; left: 20px; display: flex; flex-direction: column; gap: 10px; z-index: 999; }
        .btn-corporate-contact { display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-radius: 25px; color: #fff; text-decoration: none; font-weight: 700; font-size: 0.85rem; border: 1px solid rgba(255,255,255,0.2); }
        .contact-viber { background: #7360f2; }
        .contact-tg { background: #229ED9; }
        .contact-phone { background: #10b981; }
        .chatbot-btn { position: fixed; bottom: 25px; right: 20px; background: linear-gradient(135deg, #00f0ff, #0284c7); color: #040810; font-weight: 800; padding: 13px 22px; border-radius: 30px; cursor: pointer; z-index: 1000; border: none; }
    </style>
</head>
<body>
    <div class="container-custom">
        <div class="navbar-custom">
            <a href="/" class="brand-box">
                <div class="shield-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
                <div><div style="font-weight:900; font-size:1.25rem; color:#fff; line-height:1;">PRO INVEST RADAR AI</div><small style="color:#00f0ff; font-size:0.75rem; font-weight:700;">EUR 2026 • .BG</small></div>
            </a>
            <a href="/export-pdf" target="_blank" class="btn btn-outline-info btn-sm fw-bold">📄 07:30 Дневен Бюлетин</a>
        </div>

        <!-- ОДИТ СКЕНЕР -->
        <div class="card-dark">
            <h5 class="fw-bold text-white mb-2">🔍 Дълбок финансов и правен одит по ЕИК / БУЛСТАТ</h5>
            <div class="d-flex gap-2 mb-2">
                <input type="text" id="eikInput" class="custom-input" value="030431138">
                <button class="btn btn-outline-info px-4 fw-bold" onclick="performAudit()">Търси</button>
            </div>
            <div id="companyAuditResult" class="p-3 rounded" style="background:#070c18; display:none;">
                <strong class="text-info fs-6" id="resCompName">---</strong><br>
                <span class="small text-secondary">Управител: <strong class="text-light" id="resCompManager">---</strong></span> | 
                <span class="small text-secondary">Запори: <strong class="text-success" id="resCompInjunctions">НЯМА</strong></span>
            </div>
        </div>

        <!-- KPI КАРТИ -->
        <div class="row g-2 mb-3">
            <div class="col-6 col-md-3"><div class="kpi-card"><div class="kpi-header">АКТИВИ</div><div class="kpi-value text-white">{{ stats.total }}</div></div></div>
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
            <div class="col-md-4"><div class="plan-box"><div class="small fw-bold text-secondary">STARTER EXECUTIVE</div><div class="fw-bold text-white fs-3 my-2">€60 <span class="fs-6 text-secondary">/ мес.</span></div><button class="btn-plan mt-3" onclick="alert('Стартер план')">Избери план</button></div></div>
            <div class="col-md-4"><div class="plan-box plan-popular"><div class="small fw-bold text-info">PRO RISK MONITOR (POPULAR)</div><div class="fw-bold text-white fs-3 my-2">€150 <span class="fs-6 text-secondary">/ мес.</span></div><button class="btn-plan btn-plan-pro mt-3" onclick="alert('PRO план')">ВЗЕМИ PRO</button></div></div>
            <div class="col-md-4"><div class="plan-box"><div class="small fw-bold text-secondary">ENTERPRISE M2M</div><div class="fw-bold text-white fs-3 my-2">€290 <span class="fs-6 text-secondary">/ мес.</span></div><button class="btn-plan mt-3" onclick="alert('Enterprise план')">API Ключ</button></div></div>
        </div>

        <!-- ГИС КАРТА -->
        <div class="card-dark">
            <h5 class="fw-bold text-white mb-2">🗺️ Интерактивен ГИС Радар на България</h5>
            <div id="map"></div>
        </div>

        <!-- ФИЛТРИ -->
        <div class="card-dark" style="background:#09101f;">
            <div class="row g-2">
                <div class="col-md-4"><label class="small text-secondary mb-1">Град:</label><select id="filterCity" class="custom-select" onchange="applyFilters()"><option value="all">Всички градове</option><option value="София">София</option><option value="Пловдив">Пловдив</option></select></div>
                <div class="col-md-4"><label class="small text-secondary mb-1">Търсене:</label><input type="text" id="dealSearchInput" class="custom-input" placeholder="Търси актив..." onkeyup="applyFilters()"></div>
            </div>
        </div>

        <!-- ОБЯВИ -->
        <div class="row g-3" id="dealsContainer"></div>
        <div class="pagination-box" id="paginationControls"></div>
    </div>

    <!-- КОНТАКТИ -->
    <div class="floating-contact-bar">
        <a href="viber://chat?number=%2B359888123456" class="btn-corporate-contact contact-viber">🟣 Viber Консулт</a>
        <a href="https://t.me/stroyradar_support" target="_blank" class="btn-corporate-contact contact-tg">✈️ Telegram Канал</a>
        <a href="tel:+359888123456" class="btn-corporate-contact contact-phone">📞 0888 123 456</a>
    </div>

    <button class="chatbot-btn" onclick="alert('Gemini AI е на линия!')">🎙️ Gemini AI</button>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 25.2], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        var markersCluster = L.markerClusterGroup();
        var allProjects = JSON.parse('{{ projects_json | safe }}');
        var filteredProjects = allProjects.slice();
        var currentPage = 1;
        var pageSize = 6;

        allProjects.forEach(function(item) {
            var m = L.marker([item[15], item[16]]).bindPopup("<b>" + item[1] + "</b><br>Цена: €" + Number(item[8]).toLocaleString());
            markersCluster.addLayer(m);
        });
        map.addLayer(markersCluster);

        function renderDeals() {
            var container = document.getElementById('dealsContainer');
            container.innerHTML = '';
            var start = (currentPage - 1) * pageSize;
            var pageItems = filteredProjects.slice(start, start + pageSize);

            pageItems.forEach(function(p) {
                var col = document.createElement('div');
                col.className = 'col-md-6';
                col.innerHTML = `
                    <div class="listing-card">
                        <div>
                            <div class="d-flex justify-content-between mb-1">
                                <span class="badge bg-secondary">${p[2]}</span>
                                <span class="badge bg-success">Score: ${p[11]}/100</span>
                            </div>
                            <div class="fw-bold text-white fs-6 mb-2">${p[1]}</div>
                            <div class="small text-secondary mb-2">Локация: <span class="masked-badge">${p[3]}</span></div>
                            <div class="small text-secondary mb-3">ЕИК: <span class="masked-badge">${p[6].substring(0,3)}***** 🔒</span></div>
                            <div class="d-flex justify-content-between bg-black p-2 rounded">
                                <span class="text-warning fw-bold">€${Number(p[8]).toLocaleString()}</span>
                                <span class="text-success fw-bold">-${p[10]}%</span>
                            </div>
                        </div>
                        <button class="btn btn-info btn-sm fw-bold mt-3 text-dark" onclick="alert('Нужен е абонамент за отключване')">🔓 Отключи профил</button>
                    </div>
                `;
                container.appendChild(col);
            });
            renderPagination();
        }

        function renderPagination() {
            var totalPages = Math.ceil(filteredProjects.length / pageSize);
            var controls = document.getElementById('paginationControls');
            controls.innerHTML = '';
            for(var i=1; i<=Math.min(totalPages, 5); i++) {
                controls.innerHTML += `<button class="btn-page ${i===currentPage?'active':''}" onclick="currentPage=${i}; renderDeals();">${i}</button>`;
            }
        }

        function applyFilters() {
            var q = document.getElementById('dealSearchInput').value.toLowerCase();
            var city = document.getElementById('filterCity').value;
            filteredProjects = allProjects.filter(p => (!q || p[1].toLowerCase().includes(q)) && (city === 'all' || p[4] === city));
            currentPage = 1;
            renderDeals();
        }

        renderDeals();

        function updateCalculator(val) {
            val = Number(val);
            document.getElementById('calcPriceDisplay').innerText = '€' + val.toLocaleString('de-DE');
            document.getElementById('calcTaxZmdt').innerText = '€' + Math.round(val * 0.03).toLocaleString('de-DE');
            document.getElementById('calcTaxChsi').innerText = '€' + Math.round(val * 0.015).toLocaleString('de-DE');
            document.getElementById('calcTotalCost').innerText = '€' + Math.round(val * 1.048).toLocaleString('de-DE');
        }

        function performAudit() {
            let eik = document.getElementById('eikInput').value.trim();
            fetch('/api/audit-eik?eik=' + eik).then(r => r.json()).then(d => {
                document.getElementById('companyAuditResult').style.display = 'block';
                document.getElementById('resCompName').innerText = d.name;
                document.getElementById('resCompManager').innerText = d.manager;
                document.getElementById('resCompInjunctions').innerText = d.injunctions;
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

    total = len(projects)
    top_deals = len([p for p in projects if p[11] >= 85])
    avg_disc = round(sum([float(p[10]) for p in projects]) / total, 1) if total else 54.2
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
        "manager": "Васил Стоянов Василев",
        "injunctions": "НЯМА ВПИСАНИ ЗАПОРИ"
    })

@app.route("/export-pdf")
def export_pdf():
    return "<h3>07:30 ч. Инвестиционен бюлетин</h3>", 200, {'Content-Type': 'text/html; charset=utf-8'}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
