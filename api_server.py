import os
import io
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, jsonify, Response

app = Flask(__name__)
app.secret_key = "pro-invest-radar-secure-2026-restored"
DB_PATH = "stroy_radar_intel.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS radar_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, location TEXT,
        investor TEXT, eik TEXT, price_eur REAL, market_val REAL, discount_pct REAL,
        deal_score INTEGER, status TEXT, lat REAL, lng REAL, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute("SELECT count(*) FROM radar_projects")
    if c.fetchone()[0] == 0:
        c.executemany('''INSERT INTO radar_projects 
            (title, category, location, investor, eik, price_eur, market_val, discount_pct, deal_score, status, lat, lng)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', [
            ('Многофамилна сграда "Елит Резидънс"', 'Разрешително ЗУТ', 'София, бул. Черни Връх', 'Елит Строй Билдинг ООД', '205849120', 1850000, 3200000, 42.1, 94, 'Разрешение в сила', 42.6622, 23.3185),
            ('Логистичен хъб "Тракия Изток"', 'ЧСИ Търг', 'Пловдив, ИЗ Тракия', 'Инвест Лоджистикс ЕООД', '201984532', 1240000, 3100000, 60.0, 91, 'Публична продан', 42.1354, 24.7453)
        ])
    conn.commit()
    conn.close()

init_db()

HTML_FULL = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PRO INVEST RADAR .BG – Premium Intelligence</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        :root { --bg: #070b14; --card-bg: #0f172a; --border: #1e293b; --accent: #06b6d4; --success: #10b981; --warning: #f59e0b; }
        body { background-color: var(--bg); color: #f8fafc; font-family: -apple-system, sans-serif; padding-bottom: 50px; }
        .main-shell { max-width: 580px; margin: 0 auto; padding: 0 12px; position: relative; }
        
        .navbar-box { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 15px; }
        .btn-hamburger { background: #1e293b; border: 1px solid #334155; color: #fff; padding: 8px 12px; border-radius: 10px; font-size: 1.2rem; cursor: pointer; }

        .sat-hud-floating { position: fixed; top: 80px; right: 20px; width: 140px; height: 140px; background: radial-gradient(circle, #1e293b 0%, #0f172a 100%); border: 1px solid rgba(6,182,212,0.4); border-radius: 50%; box-shadow: 0 0 30px rgba(6,182,212,0.2); z-index: 1000; display: flex; align-items: center; justify-content: center; }
        @keyframes radarRotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes satOrbitAnim { 0% { transform: rotate(0deg) translateX(45px) rotate(0deg); } 100% { transform: rotate(360deg) translateX(45px) rotate(-360deg); } }
        .radar-sweep { transform-origin: 70px 70px; animation: radarRotate 4s linear infinite; }
        .sat-orbit { transform-origin: 70px 70px; animation: satOrbitAnim 7s linear infinite; }

        .card-custom { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 16px; margin-bottom: 14px; }
        .custom-input { background: #070b14; border: 1px solid var(--border); color: #fff; padding: 10px 14px; border-radius: 10px; width: 100%; font-family: monospace; }
        #map { height: 300px; width: 100%; border-radius: 14px; border: 1px solid var(--border); }
    </style>
</head>
<body>
    <!-- ПЛАВАЩ 3D САТЕЛИТ ВДЯСНО -->
    <div class="sat-hud-floating">
        <svg viewBox="0 0 140 140" width="120" height="120">
            <circle cx="70" cy="70" r="60" fill="none" stroke="#1e293b" stroke-width="1" stroke-dasharray="3 3"/>
            <g class="radar-sweep"><path d="M 70 70 L 25 25 A 60 60 0 0 1 115 25 Z" fill="rgba(6,182,212,0.15)"/></g>
            <circle cx="70" cy="70" r="7" fill="#0284c7"/><circle cx="70" cy="70" r="60" fill="none" stroke="var(--accent)" stroke-width="1" style="animation: pulse 2s infinite;"/>
            <g class="sat-orbit"><circle cx="70" cy="70" r="5" fill="#38bdf8"/><rect x="63" y="67" width="14" height="4" fill="#070b14" stroke="#38bdf8" rx="1"/></g>
        </svg>
    </div>

    <div class="main-shell">
        <!-- НАВИГАЦИЯ С МОБИЛНО МЕНЮ ГОРЕ ВДЯСНО -->
        <div class="navbar-box">
            <div class="d-flex align-items-center gap-2">
                <span style="color:var(--success); font-size:1.1rem;">●</span>
                <span class="fw-bold text-white fs-5">PRO INVEST <span class="text-info">RADAR .BG</span></span>
            </div>
            <button class="btn-hamburger" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileMenu">☰</button>
        </div>

        <!-- ЕИК СКЕНЕР С ДЕТАЙЛИ ОТДОЛУ -->
        <div class="card-custom">
            <h6 class="fw-bold text-white mb-2">🏢 Пълен Одит по ЕИК / БУЛСТАТ</h6>
            <div class="d-flex gap-2 mb-3">
                <input type="text" id="bulstatInput" class="custom-input" placeholder="Въведете ЕИК (напр. 205849120)..." value="205849120">
                <button class="btn btn-outline-info" style="border-radius:10px;" onclick="lookupBulstat()">Търси</button>
            </div>
            <div id="companyReport" class="p-3 rounded" style="background:#070b14; border:1px solid #1e293b; display:none;">
                <div class="d-flex justify-content-between mb-2"><strong><span class="text-info" id="compName"></span></strong><span class="badge bg-success">АКТИВЕН</span></div>
                <div class="small text-secondary mb-1">Управител: <strong class="text-light" id="compManager"></strong></div>
                <div class="small text-secondary mb-2">Вписани запори: <strong class="text-success" id="compInjunctions">НЯМА</strong></div>
            </div>
        </div>

        <!-- КАРТА -->
        <div class="card-custom"><h6 class="fw-bold text-white mb-2">🗺️ Интерактивна ГИС Карта</h6><div id="map"></div></div>
    </div>

    <!-- МОБИЛНО МЕНЮ (OFFCANVAS) -->
    <div class="offcanvas offcanvas-end text-bg-dark" tabindex="-1" id="mobileMenu" style="background-color:#0d1527!important;border-left:1px solid #1e293b;">
        <div class="offcanvas-header border-bottom border-secondary"><h5 class="offcanvas-title text-info">📡 МЕНЮ</h5><button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas"></button></div>
        <div class="offcanvas-body d-flex flex-column gap-3">
            <a href="/" class="btn btn-outline-light text-start">🏠 Радар</a>
            <a href="/export-pdf" target="_blank" class="btn btn-outline-light text-start">📄 PDF Доклад</a>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 24.5], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        
        function lookupBulstat() {
            var eik = document.getElementById('bulstatInput').value.trim();
            if(!eik) return;
            document.getElementById('companyReport').style.display = 'block';
            document.getElementById('compName').innerText = (eik === '205849120') ? 'Елит Строй Билдинг ООД' : 'Фирма '+eik;
            document.getElementById('compManager').innerText = 'Инж. Димитър Георгиев';
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home(): return render_template_string(HTML_FULL)

@app.route("/export-pdf")
def export_pdf(): return "<script>window.print();</script><h2>Доклад</h2>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
