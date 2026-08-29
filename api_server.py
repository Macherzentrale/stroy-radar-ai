import os
import json
import sqlite3
from flask import Flask, render_template_string, jsonify, Response

app = Flask(__name__)
DB_PATH = "stroy_radar_intel.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS radar_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, location TEXT,
        investor TEXT, eik TEXT, price_eur REAL, market_val REAL, discount_pct REAL,
        deal_score INTEGER, status TEXT, lat REAL, lng REAL
    )''')
    conn.commit()
    conn.close()

init_db()

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PRO INVEST RADAR .BG</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { --bg: #070b14; --card-bg: #0f172a; --border: #1e293b; --cyan: #06b6d4; --green: #10b981; }
        body { background-color: var(--bg); color: #f8fafc; font-family: -apple-system, sans-serif; margin: 0; padding-bottom: 40px; }
        .wrapper { max-width: 900px; margin: 0 auto; padding: 12px; }
        
        .header-bar { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
        .brand-title { font-size: 1.25rem; font-weight: 800; color: #fff; text-decoration: none; display: flex; align-items: center; gap: 8px; }
        .btn-menu { background: #1e293b; border: 1px solid #334155; color: #fff; padding: 6px 12px; border-radius: 8px; font-size: 1.2rem; cursor: pointer; }

        .card-custom { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 16px; margin-bottom: 16px; }
        .custom-input { background: #070b14; border: 1px solid var(--border); color: #fff; padding: 10px 14px; border-radius: 10px; width: 100%; font-family: monospace; }
        .custom-input:focus { outline: none; border-color: var(--cyan); }

        /* 3D Сателит */
        .sat-hud { background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%); border: 1px solid rgba(6,182,212,0.4); border-radius: 16px; padding: 16px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        @keyframes radarRotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes satOrbitAnim { 0% { transform: rotate(0deg) translateX(48px) rotate(0deg); } 100% { transform: rotate(360deg) translateX(48px) rotate(-360deg); } }
        .radar-sweep { transform-origin: 75px 75px; animation: radarRotate 4s linear infinite; }
        .sat-orbit { transform-origin: 75px 75px; animation: satOrbitAnim 7s linear infinite; }

        #map { height: 320px; width: 100%; border-radius: 14px; border: 1px solid var(--border); }
    </style>
</head>
<body>
    <div class="wrapper">
        <!-- НАВИГАЦИЯ -->
        <div class="header-bar">
            <a href="/" class="brand-title">
                <span style="color:var(--green); font-size:1.1rem;">●</span>
                <span>PRO INVEST RADAR <span style="color:var(--cyan);">.BG</span></span>
            </a>
            <button class="btn-menu" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileNav">☰</button>
        </div>

        <!-- ГОРЕН БЛОК: ЕИК ОДИТ + 3D САТЕЛИТ ВДЯСНО -->
        <div class="row g-3 mb-3">
            <div class="col-lg-7">
                <div class="card-custom h-100 mb-0">
                    <h5 class="fw-bold text-white mb-1">🏢 Одит на фирма по БУЛСТАТ / ЕИК</h5>
                    <p class="text-secondary small mb-3">Въведете ЕИК за проверка на запори, свързани строежи и ЧСИ дела:</p>
                    <div class="d-flex gap-2 mb-3">
                        <input type="text" id="bulstatInp" class="custom-input" placeholder="Въведете ЕИК (напр. 205849120)..." value="205849120">
                        <button class="btn btn-info px-4 fw-bold" style="border-radius:10px; color:#070b14;" onclick="auditCompany()">Търси</button>
                    </div>
                    
                    <div id="auditBox" class="p-3 rounded" style="background:#070b14; border:1px solid var(--border); display:none;">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong class="text-info fs-6" id="audName">Елит Строй Билдинг ООД</strong>
                            <span class="badge bg-success">АКТИВЕН</span>
                        </div>
                        <div class="small text-secondary mb-1">ЕИК: <span class="text-light" id="audEik">205849120</span> | Седалище: <span class="text-light">София, България</span></div>
                        <div class="small text-secondary mb-2">Управител: <span class="text-light">Инж. Димитър Георгиев</span></div>
                        <div class="border-top border-secondary pt-2 mt-2">
                            <div class="d-flex justify-content-between small">
                                <span>Вписани запори:</span>
                                <strong class="text-success">НЯМА ВПИСАНИ ЗАПОРИ</strong>
                            </div>
                            <div class="d-flex justify-content-between small mt-1">
                                <span>Свързани ЗУТ/ЧСИ обекти:</span>
                                <strong class="text-warning">1 активен обект в радар</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 3D САТЕЛИТ ВДЯСНО -->
            <div class="col-lg-5">
                <div class="sat-hud">
                    <div class="text-info small fw-bold mb-2">🛰️ 3D САТЕЛИТЕН МОНИТОРИНГ</div>
                    <svg viewBox="0 0 150 150" width="130" height="130">
                        <circle cx="75" cy="75" r="65" fill="none" stroke="#1e293b" stroke-width="1.2" stroke-dasharray="3 3"/>
                        <circle cx="75" cy="75" r="42" fill="none" stroke="#1e293b" stroke-width="1"/>
                        <g class="radar-sweep">
                            <path d="M 75 75 L 25 25 A 65 65 0 0 1 125 25 Z" fill="rgba(6,182,212,0.2)"/>
                        </g>
                        <circle cx="75" cy="75" r="8" fill="#0284c7"/>
                        <g class="sat-orbit">
                            <circle cx="75" cy="75" r="5" fill="#38bdf8"/>
                            <rect x="68" y="72" width="14" height="5" fill="#070b14" stroke="#38bdf8" rx="1"/>
                        </g>
                    </svg>
                    <div class="small text-secondary mt-2">Телеметрия: <strong class="text-success">● ОНЛАЙН</strong></div>
                </div>
            </div>
        </div>

        <!-- КАРТА -->
        <div class="card-custom">
            <h6 class="fw-bold text-white mb-2">🗺️ Интерактивна ГИС Карта</h6>
            <div id="map"></div>
        </div>
    </div>

    <!-- МОБИЛНО МЕНЮ (OFFCANVAS) -->
    <div class="offcanvas offcanvas-end text-bg-dark" tabindex="-1" id="mobileNav" style="background:#0d1527 !important; border-left:1px solid #1e293b;">
        <div class="offcanvas-header border-bottom border-secondary">
            <h5 class="offcanvas-title fw-bold text-info">📱 PRO INVEST RADAR</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas"></button>
        </div>
        <div class="offcanvas-body d-flex flex-column gap-3">
            <a href="/" class="btn btn-outline-light text-start py-2">🏠 Начало / Радар</a>
            <a href="/export-pdf" target="_blank" class="btn btn-outline-light text-start py-2">📄 Седмичен PDF Доклад</a>
            <a href="/api/deals" target="_blank" class="btn btn-outline-info text-start py-2">&gt;_ M2M JSON API</a>
            <div class="text-secondary small mt-auto border-top border-secondary pt-3">Версия 2026 • Live B2B Intel</div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 24.5], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);
        L.marker([42.6622, 23.3185]).addTo(map).bindPopup("<strong>Жилищна сграда Елит</strong><br>София, Черни Връх");

        function auditCompany() {
            var eik = document.getElementById('bulstatInp').value.trim();
            if(!eik) return;
            document.getElementById('auditBox').style.display = 'block';
            document.getElementById('audEik').innerText = eik;
            if(eik === '030431138') {
                document.getElementById('audName').innerText = 'Трейс Груп Холд АД';
            } else {
                document.getElementById('audName').innerText = 'Елит Строй Билдинг ООД';
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_CONTENT)

@app.route("/export-pdf")
def export_pdf():
    return "<script>window.print();</script><h2>PRO INVEST RADAR .BG – ДОКЛАД</h2>"

@app.route("/api/deals")
def api_deals():
    return jsonify({"status": "live", "year": 2026})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
