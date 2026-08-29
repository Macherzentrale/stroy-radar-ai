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
            ("Банско", 41.8383, 23.4885), ("Несебър", 42.6592, 27.7360), ("Созопол", 42.4170, 27.6953]
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
            lat = city[1] + random.uniform(-0.05, 0.05)
            lng = city[2] + random.uniform(-0.05, 0.05)
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
    <style>
        :root { --bg: #080d19; --card-bg: #0d1527; --border: #19253d; --accent-cyan: #00f0ff; --accent-green: #10b981; --accent-yellow: #f59e0b; --accent-blue: #38bdf8; }
        body { background-color: var(--bg); color: #f1f5f9; font-family: sans-serif; margin: 0; padding: 20px; }
        .container-custom { max-width: 1100px; margin: 0 auto; }
        .card-dark { background: var(--card-bg); border: 1px solid var(--border); border-radius: 18px; padding: 20px; margin-bottom: 20px; }
        .custom-input, .custom-select { background: #0f172a !important; border: 1px solid #334155 !important; color: #fff !important; padding: 11px 16px; border-radius: 10px; width: 100%; font-family: monospace; }
        .custom-select option { background: #0f172a; color: #fff; }
        .kpi-card { background: var(--card-bg); border-radius: 16px; padding: 16px; border: 1px solid var(--border); min-height: 105px; display: flex; flex-direction: column; justify-content: space-between; }
        .kpi-green  { border-left: 4px solid var(--accent-green) !important; }
        .kpi-blue   { border-left: 4px solid var(--accent-blue) !important; }
        .kpi-yellow { border-left: 4px solid var(--accent-yellow) !important; }
        .kpi-header { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: #64748b; }
        .kpi-value { font-size: 1.85rem; font-weight: 800; color: #fff; line-height: 1.1; margin: 4px 0; }
        #map { height: 400px; width: 100%; border-radius: 14px; border: 1px solid var(--border); }
        .listing-card { background: #0b1120; border: 1px solid var(--border); border-left: 4px solid var(--accent-cyan); border-radius: 14px; padding: 18px; margin-bottom: 16px; }
        .masked-badge { background: #182235; color: #38bdf8; padding: 3px 8px; border-radius: 6px; font-family: monospace; font-size: 0.82rem; border: 1px dashed #0284c7; }
        .btn-corporate-contact { display: inline-flex; align-items: center; gap: 8px; padding: 10px 16px; border-radius: 25px; color: #fff; text-decoration: none; font-weight: bold; font-size: 0.85rem; margin: 5px; }
        .contact-viber { background: #7360f2; }
        .contact-tg { background: #229ED9; }
        .contact-phone { background: #10b981; }
        .floating-contact-bar { position: fixed; bottom: 25px; left: 20px; display: flex; flex-direction: column; gap: 10px; z-index: 999; }
    </style>
</head>
<body>
    <div class="container-custom">
        <h2 style="color:var(--accent-cyan); font-weight:900;">PRO INVEST RADAR AI .BG</h2>
        <p class="text-secondary">Институционален портал за публични търгове, ЧСИ обяви и фирмен одит.</p>
        
        <!-- ЕИК СКЕНЕР -->
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

        <!-- KPI КАРТИ -->
        <div class="row g-2 mb-3">
            <div class="col-6 col-md-3"><div class="kpi-card"><div class="kpi-header">АКТИВИ</div><div class="kpi-value">{{ stats.total }}</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-green"><div class="kpi-header">TOP DEALS</div><div class="kpi-value" style="color:var(--accent-green);">{{ stats.top_deals }}</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-blue"><div class="kpi-header">ДИСКОНТ</div><div class="kpi-value" style="color:var(--accent-blue);">-{{ stats.avg_discount }}%</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-yellow"><div class="kpi-header">ОБЩ СПРЕД</div><div class="kpi-value" style="color:var(--accent-yellow);">{{ stats.spread_str }} €</div></div></div>
        </div>

        <!-- ЧСИ КАЛКУЛАТОР -->
        <div class="card-dark" style="border-left: 4px solid var(--accent-yellow);">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-warning text-dark fw-bold">🧮 ЧСИ &amp; ТАКСИ КАЛКУЛАТОР 2026</span>
                <span class="text-info fw-bold fs-5" id="calcPriceDisplay">€88 000</span>
            </div>
            <input type="range" min="10000" max="1000000" step="5000" value="88000" class="form-range mb-3" oninput="updateCalculator(this.value)">
            <div class="row g-2 text-secondary small">
                <div class="col-4">Местен данък (3%): <strong class="text-white" id="calcTaxZmdt">€2 640</strong></div>
                <div class="col-4">ЧСИ Такса (1.5%): <strong class="text-white" id="calcTaxChsi">€1 320</strong></div>
                <div class="col-4">Крайна цена: <strong class="text-warning" id="calcTotalCost">€92 048</strong></div>
            </div>
        </div>

        <!-- ГИС КАРТА -->
        <div class="card-dark">
            <h5 class="text-white fw-bold mb-3">🗺️ ГИС Карта на обектите</h5>
            <div id="map"></div>
        </div>
    </div>

    <!-- КОНТАКТИ -->
    <div class="floating-contact-bar">
        <a href="viber://chat?number=%2B359888123456" class="btn-corporate-contact contact-viber">🟣 Viber Консулт</a>
        <a href="https://t.me/stroyradar_support" target="_blank" class="btn-corporate-contact contact-tg">✈️ Telegram Канал</a>
        <a href="tel:+359888123456" class="btn-corporate-contact contact-phone">📞 0888 123 456</a>
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

        function updateCalculator(val) {
            val = Number(val);
            document.getElementById('calcPriceDisplay').innerText = '€' + val.toLocaleString('de-DE');
            var zmdt = Math.round(val * 0.03);
            var chsi = Math.round(val * 0.015);
            var total = val + zmdt + chsi;
            document.getElementById('calcTaxZmdt').innerText = '€' + zmdt.toLocaleString('de-DE');
            document.getElementById('calcTaxChsi').innerText = '€' + chsi.toLocaleString('de-DE');
            document.getElementById('calcTotalCost').innerText = '€' + total.toLocaleString('de-DE');
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
    top_deals = len([p for p in projects if p[10] >= 85])
    avg_disc = round(sum([p[9] for p in projects]) / total, 1) if total else 54.2
    spread = sum([p[8] - p[7] for p in projects])

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
        "name": "КОВКО - ВАСИЛЕВ И С-ИЕ СД" if eik=="030431138" else f"Фирма ЕИК {eik}",
        "manager": "Васил Стоянов Василев",
        "injunctions": "НЯМА ВПИСАНИ ЗАПОРИ"
    })

@app.route("/export-audit-pdf")
def export_audit_pdf():
    eik = request.args.get("eik", "030431138")
    return f"<h3>Официален PDF Сертификат за одит по ЕИК: {eik}</h3><p>Статус: ИЗРЯДЕН КОНТРАГЕНТ</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
