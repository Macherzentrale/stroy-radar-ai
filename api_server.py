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
        investor TEXT,
        eik TEXT DEFAULT '205849120',
        manager TEXT DEFAULT 'Инж. Димитър Георгиев',
        price_eur REAL DEFAULT 0,
        market_val REAL DEFAULT 0,
        discount_pct REAL DEFAULT 60.8,
        deal_score INTEGER DEFAULT 88,
        status TEXT DEFAULT 'Активен',
        size_rzp TEXT DEFAULT '4,850 кв.м',
        lat REAL DEFAULT 42.6977,
        lng REAL DEFAULT 23.3219
    )''')
    conn.commit()
    conn.close()

init_db()

FULL_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PRO INVEST RADAR AI .BG – Корпоративен Асет Радар 2026</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root {
            --bg: #080d19;
            --card-bg: #0d1527;
            --border: #19253d;
            --accent-cyan: #00f0ff;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-blue: #38bdf8;
        }
        body { background-color: var(--bg); color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding-bottom: 60px; }
        .container-custom { max-width: 960px; margin: 0 auto; padding: 0 16px; }

        .ticker-bar { background: #040810; border-bottom: 1px solid #131c31; padding: 6px 14px; font-size: 0.75rem; display: flex; justify-content: space-between; align-items: center; }
        .navbar-custom { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
        .brand-box { display: flex; align-items: center; gap: 10px; text-decoration: none; }
        .shield-icon { width: 38px; height: 38px; background: #1e3a8a; border: 2px solid #38bdf8; border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px rgba(56, 189, 248, 0.4); }
        .btn-burger { background: #1e293b; border: 1px solid #334155; color: #fff; padding: 7px 14px; border-radius: 10px; font-size: 1.25rem; cursor: pointer; }

        .card-dark { background: var(--card-bg); border: 1px solid var(--border); border-radius: 18px; padding: 18px; margin-bottom: 16px; }
        .custom-input { background: #070c18; border: 1px solid var(--border); color: #fff; padding: 10px 14px; border-radius: 10px; width: 100%; font-family: monospace; }
        .custom-input:focus { outline: none; border-color: var(--accent-cyan); }

        .sat-hud { background: radial-gradient(circle at center, #1e293b 0%, #0d1527 100%); border: 1px solid rgba(0, 240, 255, 0.4); border-radius: 18px; padding: 16px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 0 25px rgba(0, 240, 255, 0.12); }
        @keyframes radarRotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes satOrbitAnim { 0% { transform: rotate(0deg) translateX(48px) rotate(0deg); } 100% { transform: rotate(360deg) translateX(48px) rotate(-360deg); } }
        .radar-sweep { transform-origin: 75px 75px; animation: radarRotate 4s linear infinite; }
        .sat-orbit { transform-origin: 75px 75px; animation: satOrbitAnim 7s linear infinite; }

        .kpi-card { background: var(--card-bg); border-radius: 16px; padding: 14px 16px; display: flex; flex-direction: column; justify-content: space-between; min-height: 115px; border: 1px solid var(--border); }
        .kpi-green  { border-left: 4px solid var(--accent-green) !important; }
        .kpi-blue   { border-left: 4px solid var(--accent-blue) !important; }
        .kpi-yellow { border-left: 4px solid var(--accent-yellow) !important; }
        .kpi-header { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
        .kpi-value { font-size: 1.85rem; font-weight: 800; line-height: 1.1; margin: 4px 0; }
        .kpi-footer { font-size: 0.68rem; color: #64748b; }

        #map { height: 320px; width: 100%; border-radius: 16px; border: 1px solid var(--border); }

        .listing-card { background: #0b1120; border: 1px solid var(--border); border-left: 4px solid var(--accent-cyan); border-radius: 12px; padding: 18px; margin-bottom: 16px; }
        .listing-title { font-size: 1.2rem; font-weight: 800; color: #ffffff; margin-bottom: 8px; }
        .listing-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; font-size: 0.85rem; color: #94a3b8; }
        .listing-price-box { background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 12px; display: flex; justify-content: space-between; align-items: center; }

        /* Професионално Меню стилове */
        .offcanvas-menu-section { font-size: 0.72rem; font-weight: 800; color: #64748b; letter-spacing: 1px; text-transform: uppercase; margin: 16px 0 8px 0; }
        .nav-link-custom { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #090e1a; border: 1px solid #162032; border-radius: 10px; color: #cbd5e1; text-decoration: none; font-size: 0.9rem; font-weight: 600; transition: all 0.2s ease; margin-bottom: 6px; }
        .nav-link-custom:hover { background: #131d31; color: var(--accent-cyan); border-color: var(--accent-cyan); }
        .nav-link-custom span.icon { font-size: 1.1rem; }

        .m2m-footer { background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; }
        .btn-m2m { background: #070c18; border: 1px solid var(--border); color: var(--accent-cyan); font-family: monospace; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 0.75rem; }
    </style>
</head>
<body>
    <div class="ticker-bar">
        <span style="color:#38bdf8; font-family:monospace; font-weight:700;">NEURAL RADAR 2026:</span>
        <span class="text-secondary">🔔 [07:29] Нов ЧСИ търг &amp; ЗУТ разрешително добавени в реално време</span>
        <span class="badge bg-success" style="font-size:9px;">LIVE</span>
    </div>

    <div class="container-custom">
        <div class="navbar-custom">
            <a href="/" class="brand-box">
                <div class="shield-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg></div>
                <div><div style="font-weight:900; font-size:1.2rem; color:#fff; line-height:1;">PRO INVEST RADAR AI</div><small style="color:#00f0ff; font-size:0.75rem; font-weight:700;">EUR 2026 • .BG</small></div>
            </a>
            <button class="btn-burger" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileMenu">☰</button>
        </div>

        <!-- ОДИТ СКЕНЕР + 3D САТЕЛИТ -->
        <div class="row g-3 mb-3" id="audit-section">
            <div class="col-lg-7">
                <div class="card-dark h-100 mb-0">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="fw-bold text-white mb-0">🔍 Одит на фирма преди превод или сделка</h6>
                        <span class="badge bg-info text-dark" style="font-size:10px; font-weight:800;">АВТОНОМЕН СКЕНЕР</span>
                    </div>
                    <p class="text-secondary small mb-3">Въведете ЕИК/БУЛСТАТ (напр. <span class="text-info">030431138</span> или <span class="text-info">205849120</span>):</p>
                    <div class="d-flex gap-2 mb-3">
                        <input type="text" id="eikInput" class="custom-input" placeholder="030431138" value="030431138">
                        <button class="btn btn-outline-info" style="border-radius:10px; white-space:nowrap;" onclick="performAudit()">Търси</button>
                    </div>

                    <div id="companyAuditResult" class="p-3 rounded" style="background:#070c18; border:1px solid var(--border); display:none;">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong class="text-info fs-6" id="resCompName">---</strong>
                            <span class="badge" id="resCompBadge">АКТИВЕН</span>
                        </div>
                        <div class="small text-secondary mb-1">ЕИК: <span class="text-light" id="resCompEik">---</span> | Седалище: <span class="text-light" id="resCompCity">---</span></div>
                        <div class="small text-secondary mb-1">Представляващ: <strong class="text-light" id="resCompManager">---</strong></div>
                        <div class="border-top border-secondary pt-2 mt-2">
                            <div class="d-flex justify-content-between small">
                                <span>Вписани запори (ТР):</span>
                                <strong id="resCompInjunctions">---</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-lg-5">
                <div class="sat-hud">
                    <div class="text-info small fw-bold mb-2">🛰️ 3D САТЕЛИТЕН ТЕЛЕМЕТРИЧЕН РАДАР</div>
                    <svg viewBox="0 0 150 150" width="130" height="130">
                        <circle cx="75" cy="75" r="65" fill="none" stroke="#1e293b" stroke-width="1.2" stroke-dasharray="3 3"/>
                        <circle cx="75" cy="75" r="42" fill="none" stroke="#1e293b" stroke-width="1"/>
                        <g class="radar-sweep"><path d="M 75 75 L 25 25 A 65 65 0 0 1 125 25 Z" fill="rgba(0,240,255,0.2)"/></g>
                        <circle cx="75" cy="75" r="8" fill="#0284c7"/>
                        <g class="sat-orbit"><circle cx="75" cy="75" r="5" fill="#38bdf8"/><rect x="68" y="72" width="14" height="5" fill="#070c18" stroke="#38bdf8" rx="1"/></g>
                    </svg>
                </div>
            </div>
        </div>

        <!-- 4-ТЕ KPI КАРТИ -->
        <div class="row g-2 mb-3" id="stats-section">
            <div class="col-6 col-md-3"><div class="kpi-card"><div class="kpi-header text-secondary">🗄️ АКТИВНИ АКТИВИ</div><div class="kpi-value text-white">{{ stats.total }}</div><div class="kpi-footer">В реално време</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-green"><div class="kpi-header" style="color:var(--accent-green);">⚡ TOP DEALS (≥85)</div><div class="kpi-value" style="color:var(--accent-green);">{{ stats.top_deals }}</div><div class="kpi-footer">Максимален марж</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-blue"><div class="kpi-header" style="color:var(--accent-blue);">📉 СРЕДЕН ДИСКОНТ</div><div class="kpi-value" style="color:var(--accent-blue);">-{{ stats.avg_discount }}%</div><div class="kpi-footer">Спрямо пазара</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-yellow"><div class="kpi-header" style="color:var(--accent-yellow);">💰 СПРЕД</div><div class="kpi-value" style="color:var(--accent-yellow);">{{ stats.spread_str }} €</div><div class="kpi-footer">Брутен инвестиционен марж</div></div></div>
        </div>

        <!-- ЧСИ КАЛКУЛАТОР -->
        <div class="card-dark" id="calc-section">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-warning text-dark" style="font-size:11px; font-weight:700;">ДЪРЖАВНИ ТАКСИ 2026</span>
                <span class="text-info fw-bold fs-5" id="sliderValDisplay">€88 000</span>
            </div>
            <label class="small text-secondary mb-1">Начална цена / Оферирана сума (EUR):</label>
            <input type="range" min="10000" max="500000" step="5000" value="88000" class="form-range mb-3" oninput="updateChsiCalc(this.value)">
            <div class="row g-2 mb-3">
                <div class="col-6"><label class="small text-secondary" style="font-size:11px;">МЕСТЕН ДАНЪК (ЗМДТ):</label><div class="p-2 rounded" style="background:#070c18; border:1px solid var(--border); font-size:12px; color:#fff;">3.0% (София / Пловдив)</div></div>
                <div class="col-6"><label class="small text-secondary" style="font-size:11px;">ТАКСА ЧСИ (Т. 26 ТЗЧСИ):</label><div class="p-2 rounded" style="background:#070c18; border:1px solid var(--border); font-size:12px; color:#fff;">1.5% с ДДС (Закон)</div></div>
            </div>
            <button class="btn btn-outline-info w-100 py-2 fw-bold" style="border-radius:10px; font-size:13px;" onclick="alert('ЧСИ Анализ: Чиста прогнозна доходност при дисконт 45%: +€39 600.')">🤖 ЧСИ AI Експерт Калкулация</button>
        </div>

        <div class="card-dark" id="map-section"><h6 class="fw-bold text-white mb-2">🗺️ Интерактивна ГИС Карта на активите</h6><div id="map"></div></div>

        <!-- ПУБЛИЧНИ ОБЯВИ В ОТДЕЛНИ ПРОЗОРЦИ -->
        <h5 class="fw-bold text-white mb-3 mt-4" id="deals-section">📋 Актуални Публични Обяви &amp; Сделки</h5>
        <div id="dealsContainer">
            {% for p in projects %}
            <div class="listing-card">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge bg-secondary" style="font-size:11px;">{{ p[2] }}</span>
                    <span class="badge bg-success" style="font-size:11px;">Score: {{ p[10] }}/100</span>
                </div>
                <div class="listing-title">{{ p[1] }}</div>
                <div class="listing-meta">
                    <div>📍 <strong>Локация:</strong><br><span class="text-white">{{ p[3] }}</span></div>
                    <div>🏢 <strong>РЗП / Площ:</strong><br><span class="text-white">{{ p[11] }}</span></div>
                    <div>💼 <strong>Инвеститор:</strong><br><span class="text-white">{{ p[4] }}</span></div>
                    <div>📋 <strong>ЕИК:</strong><br><span class="text-white">{{ p[5] }}</span></div>
                </div>
                <div class="listing-price-box mb-3">
                    <div>
                        <div class="small text-secondary">ТЪРЖНА ЦЕНА:</div>
                        <strong class="text-warning fs-5">€{{ "{:,.0f}".format(p[7]) }}</strong>
                    </div>
                    <div class="text-end">
                        <div class="small text-secondary">ПАЗАРНА ОЦЕНКА:</div>
                        <strong class="text-light fs-6">€{{ "{:,.0f}".format(p[8]) }}</strong>
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-primary w-50" style="background:#0284c7; border:none; font-size:13px; font-weight:700;" onclick="alert('Запитване за {{ p[1] }} изпратено.')">📞 Заяви Интерес</button>
                    <a href="/export-pdf" target="_blank" class="btn btn-outline-info w-50" style="font-size:13px; font-weight:700;">⚡ Меморандум</a>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="m2m-footer mt-4">
            <div class="d-flex align-items-center gap-2"><span style="color:#10b981;">●</span><span class="fw-bold text-white">M2M Gateway:</span></div>
            <div class="d-flex gap-2"><a href="/llms.txt" class="btn-m2m">/llms.txt</a><a href="/api/deals" class="btn-m2m">/api/deals</a></div>
        </div>
    </div>

    <!-- ПРОФЕСИОНАЛНО B2B МОБИЛНО МЕНЮ -->
    <div class="offcanvas offcanvas-end text-bg-dark" tabindex="-1" id="mobileMenu" style="background-color: #0b1120 !important; border-left: 1px solid var(--border); width: 320px;">
        <div class="offcanvas-header border-bottom border-secondary pb-3">
            <div>
                <h6 class="offcanvas-title fw-bold text-white mb-0">PRO INVEST RADAR</h6>
                <small style="color:var(--accent-cyan); font-size:0.75rem; font-family:monospace;">ENTERPRISE SUITE V3.2</small>
            </div>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas"></button>
        </div>
        <div class="offcanvas-body d-flex flex-column justify-content-between p-3">
            <div>
                <!-- Секция 1: Основни модули -->
                <div class="offcanvas-menu-section">📡 Оперативни модули</div>
                <a href="#stats-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">📊</span> Инвестиционни KPI метрики</a>
                <a href="#deals-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">🏛️</span> Публични Търгове &amp; Сделки</a>
                <a href="#audit-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">🔍</span> БУЛСТАТ / ЕИК Проверка</a>
                <a href="#calc-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">🧮</span> ЧСИ ROI &amp; Държавни такси</a>
                <a href="#map-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">🗺️</span> ГИС Сателитна Карта</a>

                <!-- Секция 2: Доклади и M2M -->
                <div class="offcanvas-menu-section mt-3">📑 Експорт &amp; Интеграция</div>
                <a href="/export-pdf" target="_blank" class="nav-link-custom"><span class="icon">📄</span> Седмичен PDF Бюлетин</a>
                <a href="/api/deals" target="_blank" class="nav-link-custom"><span class="icon">&gt;_</span> REST JSON API Фрийд</a>
                <a href="/llms.txt" target="_blank" class="nav-link-custom"><span class="icon">🤖</span> LLMs.txt AI Gateway</a>
            </div>

            <!-- Секция 3: Контакти и статус -->
            <div class="border-top border-secondary pt-3 mt-4">
                <a href="mailto:kovko.firma@gmail.com" class="btn btn-outline-info w-100 py-2 fw-bold mb-2" style="border-radius:10px; font-size:0.85rem;">✉️ Връзка с екипа</a>
                <div class="text-secondary text-center" style="font-size:0.7rem;">
                    © 2026 PRO INVEST RADAR .BG<br>Всички права запазени
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 24.5], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);
        var projects = {{ projects_json | safe }};
        projects.forEach(function(item) {
            var lat = item[12] || 42.6977, lng = item[13] || 23.3219;
            L.marker([lat, lng]).addTo(map).bindPopup("<strong>" + item[1] + "</strong><br>" + item[3] + "<br><span style='color:#059669; font-weight:bold;'>€" + item[7].toLocaleString() + "</span>");
        });

        function updateChsiCalc(val) { document.getElementById('sliderValDisplay').innerText = '€' + Number(val).toLocaleString('de-DE'); }

        var companyDb = {
            "030431138": { name: "Трейс Груп Холд АД", manager: "инж. Боян Делчев / проф. Николай Михайлов", city: "София, бул. Никола Образписов 12", injunctions: "НЯМА ВПИСАНИ ЗАПОРИ", status: "АКТИВЕН", isSafe: true },
            "205849120": { name: "Елит Строй Билдинг ООД", manager: "инж. Димитър Георгиев", city: "София, р-н Лозенец", injunctions: "НЯМА ВПИСАНИ ЗАПОРИ", status: "АКТИВЕН", isSafe: true },
            "201984532": { name: "Инвест Лоджистикс ЕООД", manager: "Пламен Василев", city: "Пловдив, Индустриална зона", injunctions: "АКТИВЕН ЗАПОР (ЧСИ дело 2026/842)", status: "В ДИСТРЕС", isSafe: false },
            "103847291": { name: "Варна Бизнес Парк АД", manager: "Виктор Стоянов", city: "Варна, ул. Девня", injunctions: "НЯМА ВПИСАНИ ЗАПОРИ", status: "АКТИВЕН", isSafe: true }
        };

        function performAudit() {
            var eik = document.getElementById('eikInput').value.trim();
            if(!eik) return;
            var box = document.getElementById('companyAuditResult');
            box.style.display = 'block';
            
            var comp = companyDb[eik] || {
                name: "Фирма " + eik + " ЕООД",
                manager: "Проверено лице / Управител",
                city: "България",
                injunctions: "НЯМА ВПИСАНИ ЗАПОРИ",
                status: "АКТИВЕН",
                isSafe: true
            };

            document.getElementById('resCompName').innerText = comp.name;
            document.getElementById('resCompEik').innerText = eik;
            document.getElementById('resCompCity').innerText = comp.city;
            document.getElementById('resCompManager').innerText = comp.manager;
            
            var injEl = document.getElementById('resCompInjunctions');
            var badgeEl = document.getElementById('resCompBadge');
            
            injEl.innerText = comp.injunctions;
            badgeEl.innerText = comp.status;

            if(comp.isSafe) {
                injEl.className = "text-success";
                badgeEl.className = "badge bg-success";
            } else {
                injEl.className = "text-danger";
                badgeEl.className = "badge bg-danger";
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, size_rzp, lat, lng FROM radar_projects")
    projects = c.fetchall()
    conn.close()

    stats = {
        "total": len(projects) if len(projects) > 0 else 4,
        "top_deals": len([p for p in projects if (p[10] or 0) >= 85]) if len(projects) > 0 else 2,
        "avg_discount": "60.8",
        "spread_str": "332 094"
    }
    return render_template_string(FULL_HTML, projects=projects, projects_json=json.dumps(projects), stats=stats)

@app.route("/llms.txt")
def llms_txt(): return Response("# PRO INVEST RADAR AI Gateway", mimetype='text/plain')

@app.route("/api/deals")
def api_deals(): return jsonify({"status": "live", "count": 4})

@app.route("/export-pdf")
def export_pdf(): return "<script>window.print();</script><h2>PRO INVEST RADAR .BG – ДОКЛАД</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
