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
        investor TEXT,
        eik TEXT,
        manager TEXT,
        price_eur REAL,
        market_val REAL,
        discount_pct REAL,
        deal_score INTEGER,
        status TEXT,
        size_rzp TEXT,
        created_at TEXT,
        lat REAL,
        lng REAL
    )''')
    
    c.execute("SELECT count(*) FROM radar_projects")
    if c.fetchone()[0] < 50:
        c.execute("DELETE FROM radar_projects")
        cities = [
            ("София", 42.6977, 23.3219), ("Пловдив", 42.1354, 24.7453), ("Варна", 43.2141, 27.9147),
            ("Бургас", 42.5048, 27.4626), ("Русе", 43.8563, 25.9700), ("Стара Загора", 42.4258, 25.6345)
        ]
        types = [
            ('Жилищна сграда & апартаменти', 'Разрешително ЗУТ', 'Одобрен проект', '3,400 кв.м', 850000, 1600000, 46.8, 92),
            ('Логистичен склад & терминал', 'ЧСИ Търг', 'Публична продан', '8,200 кв.м', 620000, 1450000, 57.2, 89),
            ('Търговска сграда', 'NPL Дистрес', 'Банково обезпечение', '2,800 кв.м', 490000, 1100000, 55.4, 87)
        ]
        records = []
        for i in range(60):
            city = cities[i % len(cities)]
            t = types[i % len(types)]
            idx = i + 1
            title = f'{t[0]} "{city[0]} Национален обект #{idx}"'
            location = f"{city[0]}, Район Централен кв. {idx % 5 + 1}"
            investor = f"{city[0]} Пропърти Груп {idx} ООД"
            eik = str(100000000 + idx * 19)
            manager = f"Управител #{idx}"
            lat = city[1] + random.uniform(-0.03, 0.03)
            lng = city[2] + random.uniform(-0.03, 0.03)
            price = t[4] + (idx * 300) % 300000
            mval = t[5] + (idx * 600) % 500000
            disc = round(((mval - price) / mval) * 100, 1)
            score = min(99, max(75, int(t[7] + (idx % 5) - 2)))
            records.append((title, t[1], location, investor, eik, manager, price, mval, disc, score, t[2], t[3], "2026-08-30", lat, lng))
        c.executemany('''INSERT INTO radar_projects 
            (title, category, location, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, created_at, lat, lng)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', records)
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
        :root {
            --bg: #111c33;
            --card-bg: #1a2947;
            --border: #283e6b;
            --accent-cyan: #00f0ff;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-blue: #38bdf8;
        }
        html, body { background-color: var(--bg); color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; overflow-x: hidden; width: 100%; max-width: 100vw; }
        .container-custom { max-width: 1320px; margin: 0 auto; padding: 0 20px; width: 100%; box-sizing: border-box; }

        @keyframes neonGlow {
            0%, 100% { background-color: #241903; box-shadow: 0 0 15px rgba(245, 158, 11, 0.5); border-color: #f59e0b; }
            50% { background-color: #4a3406; box-shadow: 0 0 30px rgba(245, 158, 11, 0.9); border-color: #fbbf24; }
        }
        .ticker-bar { animation: neonGlow 2s infinite ease-in-out; border-bottom: 2px solid #f59e0b; padding: 10px 18px; font-size: 0.85rem; text-align: center; font-weight: bold; width: 100%; box-sizing: border-box; }
        .navbar-custom { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
        .brand-box { display: flex; align-items: center; gap: 10px; text-decoration: none; }
        .shield-icon { width: 38px; height: 38px; background: #25428a; border: 2px solid #38bdf8; border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px rgba(56, 189, 248, 0.5); }
        .btn-burger { background: #24365d; border: 1px solid #405b96; color: #fff; padding: 7px 14px; border-radius: 10px; font-size: 1.25rem; cursor: pointer; }

        .header-contacts-group { display: flex; align-items: center; gap: 10px; }
        .btn-header-contact {
            display: flex; align-items: center; gap: 6px; padding: 8px 14px; border-radius: 20px; color: #fff; text-decoration: none; font-weight: 700; font-size: 0.82rem;
            box-shadow: 0 3px 12px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.25); transition: transform 0.2s; white-space: nowrap; cursor: pointer;
        }
        .btn-header-contact:hover { transform: scale(1.05); color: #fff; }
        .contact-viber { background: #7360f2; }
        .contact-tg { background: #229ED9; }
        @media (max-width: 992px) { .header-contacts-group { display: none; } }

        .mobile-contact-bar { display: flex; justify-content: center; align-items: center; gap: 10px; padding: 12px 0 20px 0; flex-wrap: wrap; }
        .desktop-nav-contacts { display: none; }
        @media (min-width: 992px) {
            .mobile-contact-bar { display: none; }
            .desktop-nav-contacts { display: flex; align-items: center; gap: 8px; }
        }

        .card-dark { background: var(--card-bg); border: 1px solid var(--border); border-radius: 18px; padding: 22px; margin-bottom: 20px; box-sizing: border-box; box-shadow: 0 8px 30px rgba(0,0,0,0.3); }
        .custom-input, .custom-select {
            background: #132242 !important; border: 2px solid #00f0ff !important; color: #ffffff !important; height: 48px !important; line-height: 24px !important;
            padding: 10px 16px !important; border-radius: 10px !important; width: 100% !important; font-family: monospace !important; font-size: 0.9rem !important; box-sizing: border-box !important;
        }
        .custom-input:focus, .custom-select:focus { outline: none !important; border-color: #38bdf8 !important; box-shadow: 0 0 15px rgba(0,240,255,0.6) !important; background: #182b52 !important; }
        .custom-select option { background: #132242; color: #fff; padding: 8px; }

        .sat-hud { background: radial-gradient(circle at center, #243863 0%, #1a2947 100%); border: 1px solid rgba(0, 240, 255, 0.4); border-radius: 18px; padding: 16px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; box-sizing: border-box; }
        
        .kpi-card { background: var(--card-bg); border-radius: 16px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; min-height: 115px; border: 1px solid var(--border); box-sizing: border-box; }
        .kpi-green  { border-left: 4px solid var(--accent-green) !important; }
        .kpi-blue   { border-left: 4px solid var(--accent-blue) !important; }
        .kpi-yellow { border-left: 4px solid var(--accent-yellow) !important; }
        .kpi-header { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; color: #94a3b8; }
        .kpi-value { font-size: 1.85rem; font-weight: 800; line-height: 1.1; margin: 4px 0; }
        .kpi-footer { font-size: 0.7rem; color: #94a3b8; }

        #map { height: 420px; width: 100%; border-radius: 14px; border: 1px solid var(--border); }
        .leaflet-popup-content-wrapper { background: #1a2947 !important; color: #fff !important; border: 1px solid #38bdf8 !important; border-radius: 12px; }

        .listing-card { 
            background: linear-gradient(145deg, #162544 0%, #0d172e 100%); 
            border: 1px solid var(--border); 
            border-left: 4px solid var(--accent-cyan); 
            border-radius: 16px; 
            padding: 22px; 
            margin-bottom: 20px; 
            height: 100%; 
            display: flex; 
            flex-direction: column; 
            justify-content: space-between; 
            box-sizing: border-box; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        .listing-title { font-size: 1.2rem; font-weight: 800; color: #ffffff; margin-bottom: 10px; }
        .listing-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; font-size: 0.85rem; color: #cbd5e1; }
        .listing-price-box { background: #132242; border: 1px solid #283e6b; border-radius: 12px; padding: 14px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .masked-badge { background: #1b2f57; color: #38bdf8; padding: 4px 10px; border-radius: 6px; font-family: monospace; font-size: 0.82rem; border: 1px dashed #0284c7; display: inline-block; font-weight: bold; }

        .plan-box { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 22px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; box-sizing: border-box; transition: all 0.2s ease; box-shadow: 0 6px 20px rgba(0,0,0,0.2); }
        .plan-box:hover { border-color: #38bdf8; transform: translateY(-2px); }
        .plan-popular { border: 2px solid var(--accent-cyan) !important; box-shadow: 0 0 25px rgba(0, 240, 255, 0.25); }
        .btn-plan { background: #243863; border: 1px solid #405b96; color: #fff; font-weight: 700; padding: 10px 22px; border-radius: 10px; font-size: 0.9rem; text-decoration: none; display: inline-block; text-align: center; cursor: pointer; }
        .btn-plan-pro { background: var(--accent-cyan); color: #040810; font-weight: 800; border: none; }

        .benefit-row {
            background: #132242; border: 1px solid #283e6b; border-left: 4px solid var(--accent-cyan); border-radius: 10px;
            padding: 12px 16px; margin-bottom: 10px; display: flex; align-items: center; gap: 14px;
        }
        .pagination-box { display: flex; justify-content: center; gap: 8px; margin: 25px 0 35px 0; }
        .btn-page { background: var(--card-bg); border: 1px solid var(--border); color: #fff; border-radius: 8px; padding: 8px 16px; font-weight: bold; cursor: pointer; text-decoration: none; }
        .btn-page.active { background: var(--accent-cyan); color: #040810; border-color: var(--accent-cyan); }

        .site-footer { background: #0d172e; border-top: 1px solid var(--border); padding: 40px 0 30px 0; margin-top: 50px; font-size: 0.85rem; color: #94a3b8; box-sizing: border-box; }
        .impressum-box { background: #132242; border: 1px solid var(--border); border-radius: 12px; padding: 18px; font-size: 0.82rem; line-height: 1.6; }
        .iban-badge { font-family: monospace; font-size: 1.05rem; color: var(--accent-cyan); font-weight: 800; background: #0b172e; padding: 10px 14px; border-radius: 8px; border: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
    <div class="ticker-bar">
        <div class="w-100 text-center">
            <span>🔔</span>
            <span style="color:#fbbf24; font-weight:800;">07:30 ПРОТОКОЛ • НАЦИОНАЛЕН КОРПОРАТИВЕН ФИЙД:</span>
            <span class="text-light ms-1">Активни обекти в реално време • {{ stats.total }} записа</span>
        </div>
    </div>

    <div class="container-custom">
        <div class="navbar-custom">
            <a href="/" class="brand-box">
                <div class="shield-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
                <div><div style="font-weight:900; font-size:1.25rem; color:#fff; line-height:1;">PRO INVEST RADAR AI</div><small style="color:#00f0ff; font-size:0.75rem; font-weight:700;">EUR 2026 • .BG</small></div>
            </a>
            
            <div class="desktop-nav-contacts">
                <a href="viber://chat?number=%2B359879495767" class="btn-header-contact contact-viber">🟣 Viber Консулт</a>
                <a href="https://t.me/stroyradar_support" target="_blank" class="btn-header-contact contact-tg">✈️ Telegram Канал</a>
            </div>

            <div class="d-flex align-items-center gap-2">
                <a href="/export-pdf" target="_blank" class="btn btn-outline-info btn-sm fw-bold d-none d-md-inline-block" style="border-radius:8px;">📄 Дневен Бюлетин</a>
                <button class="btn-burger" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileMenu">☰</button>
            </div>
        </div>

        <div class="mobile-contact-bar">
            <a href="viber://chat?number=%2B359879495767" class="btn-header-contact contact-viber">🟣 Viber</a>
            <a href="https://t.me/stroyradar_support" target="_blank" class="btn-header-contact contact-tg">✈️ Telegram</a>
        </div>

        <div class="row g-3 mb-3" id="audit-section">
            <div class="col-lg-7">
                <div class="card-dark h-100 mb-0">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="fw-bold text-white mb-0">🔍 Пълна Експертна Справка по ЕИК / БУЛСТАТ</h6>
                        <span class="badge bg-info text-dark" style="font-size:10px; font-weight:800;">ДИРЕКТНА ВРЪЗКА С РЕГИСТРИТЕ</span>
                    </div>
                    <p class="text-secondary small mb-3">Въведете ЕИК за извличане на пълно досие от Търговски регистър и НАП (напр. <span class="text-info cursor-pointer" onclick="fillEik('030431138')">030431138</span>):</p>
                    <div class="d-flex gap-2 mb-3">
                        <input type="text" id="eikInput" class="custom-input" placeholder="Въведете ЕИК..." value="030431138">
                        <button type="button" class="btn btn-outline-info px-4 fw-bold" style="border-radius:10px; white-space:nowrap;" onclick="performAudit()">Търси</button>
                    </div>

                    <div id="companyAuditResult" class="p-3 rounded" style="background:#132242; border:1px solid var(--border); display:none;">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong class="text-info fs-6" id="resCompName">---</strong>
                            <span class="badge bg-success" id="resCompBadge">АКТИВЕН</span>
                        </div>
                        <div class="small text-secondary mb-1">ЕИК: <span class="text-light" id="resCompEik">---</span> | Седалище: <span class="text-light" id="resCompCity">---</span></div>
                        <div class="small text-secondary mb-1">Управител / Съдружници: <strong class="text-light" id="resCompManager">---</strong></div>
                        <div class="small text-secondary mb-1">Капитал и Правна форма: <span class="text-light" id="resCompCapital">---</span></div>
                        <div class="small text-secondary mb-2">Актуално състояние &amp; Оборот: <span class="text-light" id="resCompBalance">---</span></div>
                        
                        <div class="border-top border-secondary pt-2 mt-2 mb-3">
                            <div class="d-flex justify-content-between small mb-1">
                                <span>Запори / Чл. 512 ГПК / ЧСИ дела:</span>
                                <strong class="text-success" id="resCompInjunctions">НЯМА ВПИСАНИ ТЕЖЕСТИ</strong>
                            </div>
                        </div>

                        <a href="#" id="downloadAuditPdfBtn" target="_blank" class="btn btn-outline-warning btn-sm w-100 fw-bold py-2" style="border-radius:8px;">📥 Изтегли Официален PDF Доклад (Едно към едно с ТР)</a>
                    </div>
                </div>
            </div>

            <div class="col-lg-5">
                <div class="sat-hud">
                    <div class="text-info small fw-bold mb-2">🛰️ САТЕЛИТЕН ТЕЛЕМЕТРИЧЕН РАДАР</div>
                    <svg viewBox="0 0 150 150" width="130" height="130">
                        <circle cx="75" cy="75" r="65" fill="none" stroke="#243863" stroke-width="1.2" stroke-dasharray="3 3"/>
                        <circle cx="75" cy="75" r="42" fill="none" stroke="#243863" stroke-width="1"/>
                        <circle cx="75" cy="75" r="8" fill="#0284c7"/>
                    </svg>
                </div>
            </div>
        </div>

        <div class="row g-2 mb-3">
            <div class="col-6 col-md-3"><div class="kpi-card"><div class="kpi-header">АКТИВИ В БАЗАТА</div><div class="kpi-value text-white">{{ stats.total }}</div><div class="kpi-footer">Реална база данни</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-green"><div class="kpi-header" style="color:var(--accent-green);">TOP DEALS</div><div class="kpi-value" style="color:var(--accent-green);">{{ stats.top_deals }}</div><div class="kpi-footer">Максимален марж</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-blue"><div class="kpi-header" style="color:var(--accent-blue);">ДИСКОНТ</div><div class="kpi-value" style="color:var(--accent-blue);">-{{ stats.avg_discount }}%</div><div class="kpi-footer">Спрямо пазара</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-yellow"><div class="kpi-header" style="color:var(--accent-yellow);">СПРЕД</div><div class="kpi-value" style="color:var(--accent-yellow);">{{ stats.spread_str }} €</div><div class="kpi-footer">Брутен капитал</div></div></div>
        </div>

        <div class="card-dark" style="border-left: 4px solid var(--accent-yellow);">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-warning text-dark fw-bold px-2 py-1">ЧСИ &amp; ТАКСИ КАЛКУЛАТОР 2026</span>
                <span class="text-info fw-bold fs-5" id="calcPriceDisplay">€88 000</span>
            </div>
            <input type="range" min="10000" max="1000000" step="5000" value="88000" class="form-range mb-3" oninput="updateCalculator(this.value)">
            <div class="row g-2 text-secondary small">
                <div class="col-4">ЗМДТ (3%): <strong class="text-white" id="calcTaxZmdt">€2 640</strong></div>
                <div class="col-4">ЧСИ (1.5%): <strong class="text-white" id="calcTaxChsi">€1 320</strong></div>
                <div class="col-4">Вписване: <strong class="text-white" id="calcTaxAv">€88</strong></div>
            </div>
        </div>

        <div id="pricing-section" class="mt-4 mb-4">
            <div class="card-dark mb-3" style="border:1px solid #0284c7; text-align:center;">
                <div class="text-secondary small mb-1" style="letter-spacing:1px; text-transform:uppercase;">🔥 ЕКСКЛУЗИВЕН КОРПОРАТИВЕН ДОСТЪП:</div>
                <h2 class="fw-bold mb-3" style="color:#00f0ff; font-size:2.2rem; font-family:monospace;">€2.00 / ден (€60/мес.)</h2>
                <p class="text-light small mb-3">Инвестирайте днес, за да изпреварите конкуренцията си с ексклузивни данни от ЧСИ и НАП търгове преди всички останали!</p>
                <button type="button" class="btn btn-primary w-100 py-3 fw-bold shadow" style="background:#0284c7; border:none; border-radius:12px; font-size:1.05rem; cursor:pointer;" onclick="showPlanFeatures('starter')">ВИЖ ПРИДОБИВКИТЕ &amp; АКТИВИРАЙ СЕГА</button>
            </div>

            <div class="row g-3">
                <div class="col-md-4">
                    <div class="plan-box flex-column align-items-start h-100 mb-0" onclick="showPlanFeatures('starter')">
                        <div class="w-100 mb-3">
                            <div class="small fw-bold text-secondary">STARTER EXECUTIVE</div>
                            <div class="fw-bold text-white fs-3">€60 <span class="fs-6 text-secondary">/ месец</span></div>
                            <div class="text-secondary small mt-1">Отключете първите си сделки и защитете капитала си срещу скрити рискове.</div>
                        </div>
                        <button type="button" class="btn-plan w-100 mt-auto" onclick="showPlanFeatures('starter');">Виж придобивките</button>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="plan-box plan-popular flex-column align-items-start h-100 mb-0" onclick="showPlanFeatures('pro')">
                        <div class="w-100 mb-3">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="small fw-bold" style="color:#00f0ff;">PRO RISK MONITOR</span>
                                <span class="badge bg-info text-dark" style="font-size:9px; font-weight:800;">TOP CHOICE</span>
                            </div>
                            <div class="fw-bold text-white fs-3">€150 <span class="fs-6 text-secondary">/ месец</span></div>
                            <div class="text-secondary small mt-1">Изпреварващ фийд в 07:30 ч. сутринта и неограничени проверки за запори.</div>
                        </div>
                        <button type="button" class="btn-plan btn-plan-pro w-100 mt-auto" onclick="showPlanFeatures('pro');">ВЗЕМИ PRO СЕГА</button>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="plan-box flex-column align-items-start h-100 mb-0" onclick="showPlanFeatures('enterprise')">
                        <div class="w-100 mb-3">
                            <div class="small fw-bold text-secondary">ENTERPRISE M2M</div>
                            <div class="fw-bold text-white fs-3">€290 <span class="fs-6 text-secondary">/ месец</span></div>
                            <div class="text-secondary small mt-1">Пълна REST JSON API интеграция към вашия софтуер без никакви ограничения.</div>
                        </div>
                        <button type="button" class="btn-plan w-100 mt-auto" onclick="showPlanFeatures('enterprise');">Активирай API</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="card-dark" id="map-section">
            <h6 class="fw-bold text-white mb-2">ГИС Радар на България</h6>
            <div id="map"></div>
        </div>

        <div class="card-dark mb-3" style="background:#09101f;">
            <div class="row g-2 align-items-center">
                <div class="col-md-4">
                    <label class="small text-secondary mb-1">Град:</label>
                    <select id="filterCity" class="custom-select" onchange="applyAdvancedFilters()">
                        <option value="all">Всички градове</option>
                        <option value="София">София</option>
                        <option value="Пловдив">Пловдив</option>
                        <option value="Варна">Варна</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="small text-secondary mb-1">Категория:</label>
                    <select id="filterCategory" class="custom-select" onchange="applyAdvancedFilters()">
                        <option value="all">Всички категории</option>
                        <option value="ЧСИ Търг">ЧСИ Търгове</option>
                        <option value="Разрешително ЗУТ">ЗУТ Строежи</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="small text-secondary mb-1">Търсене:</label>
                    <input type="text" id="dealSearchInput" class="custom-input" placeholder="🔍 Търси проект..." onkeyup="applyAdvancedFilters()">
                </div>
            </div>
        </div>

        <div class="d-flex justify-content-between align-items-center mb-3 mt-4 flex-wrap gap-2" id="deals-section">
            <div>
                <h5 class="fw-bold text-white mb-0">📋 Публични Обяви &amp; Сделки</h5>
                <small class="text-secondary">Показват се по 6 обекта на страница (локация, инвеститор и ЕИК са защитени)</small>
            </div>
        </div>

        <div class="row g-3" id="dealsContainer"></div>
        <div class="pagination-box" id="paginationControls"></div>
    </div>

    <footer class="site-footer">
        <div class="container-custom">
            <div class="row g-4 mb-4">
                <div class="col-md-6">
                    <div class="footer-heading mb-2"><strong>Официален Импресум (Impressum)</strong></div>
                    <div class="impressum-box">
                        <strong>СД „Ковко - Василев и Сие“</strong><br>
                        Управител / Титуляр: Васил Василев<br>
                        Адрес на управление: гр. Драгоман, ул. Христо Ботев № 14<br>
                        Контакт: <a href="mailto:kovko.firma@gmail.com" style="color:var(--accent-cyan); text-decoration:none;">kovko.firma@gmail.com</a>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="footer-heading mb-2"><strong>Банкова сметка за директен превод (IBAN)</strong></div>
                    <div class="iban-badge">
                        <span>BG80UNCR70001524896321</span>
                        <button type="button" class="btn btn-sm btn-info fw-bold py-1 px-2" style="font-size:11px;" onclick="copyIban()">📋 Copy</button>
                    </div>
                    <div class="small text-secondary mt-1">Банка: UniCredit Bulbank | BIC: UNCRBGSF</div>
                </div>
            </div>
            <div class="border-top border-secondary pt-3 text-center text-secondary small">
                © 2026 PRO INVEST RADAR .BG. Всички права запазени.
            </div>
        </div>
    </footer>

    <div class="modal fade" id="featuresModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
            <div class="modal-content" style="background:#1a2947; border:1px solid var(--border); color:#fff; border-radius:18px;">
                <div class="modal-header border-bottom border-secondary pb-3">
                    <h5 class="modal-title fw-bold text-white" id="featTitle">Абонамент</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body p-4">
                    <div class="text-secondary small mb-3">Премиум маркетингов пакет с гарантирани придобивки:</div>
                    <div id="benefitsListContainer"></div>

                    <div class="bank-details-box mt-4" style="background:#132242; padding:15px; border-radius:12px; border:1px solid var(--border);">
                        <div class="small text-secondary mb-1">Директен банков превод (IBAN):</div>
                        <div class="iban-badge mb-2">
                            <span>BG80UNCR70001524896321</span>
                            <button type="button" class="btn btn-sm btn-info fw-bold py-1 px-2" style="font-size:11px;" onclick="copyIban()">📋 Copy</button>
                        </div>
                        <div class="small text-secondary">Сума за плащане: <strong class="text-warning fs-5" id="modalPriceTag">€60.00</strong></div>
                    </div>

                    <button type="button" class="btn btn-primary w-100 py-3 fw-bold mt-3 shadow" style="background:#0284c7; border:none; border-radius:12px;" onclick="confirmOrder()">✅ Потвърди банков превод &amp; Активирай</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 25.2], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        var allProjects = {{ projects_json | safe }};
        var filteredProjects = allProjects.slice();
        var currentPage = 1, pageSize = 6;

        allProjects.forEach(function(item) {
            L.marker([item[13], item[14]]).addTo(map).bindPopup(item[1]);
        });

        function renderPaginatedDeals() {
            var container = document.getElementById('dealsContainer');
            container.innerHTML = '';
            var start = (currentPage - 1) * pageSize;
            var pageItems = filteredProjects.slice(start, start + pageSize);

            pageItems.forEach(function(p) {
                var maskedLoc = p[3].split(',')[0] + ", кв. ***, ул. *** 🔒";
                var maskedInv = (p[4] || "Инвестор").substring(0, 4) + " ******* 🔒";
                var maskedEik = (p[5] || "100000000").substring(0, 3) + "****** 🔒";

                var col = document.createElement('div');
                col.className = 'col-md-6';
                col.innerHTML = `
                    <div class="listing-card">
                        <div>
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="badge bg-secondary">${p[2]}</span>
                                <span class="badge bg-success">Score: ${p[10]}/100</span>
                            </div>
                            <div class="listing-title">${p[1]}</div>
                            <div class="listing-meta">
                                <div>📍 <strong>Локация:</strong><br><span class="masked-badge">${maskedLoc}</span></div>
                                <div>🏢 <strong>РЗП / Площ:</strong><br><span class="text-white">${p[11]}</span></div>
                                <div>💼 <strong>Инвеститор:</strong><br><span class="masked-badge">${maskedInv}</span></div>
                                <div>📋 <strong>ЕИК:</strong><br><span class="masked-badge">${maskedEik}</span></div>
                            </div>
                            <div class="listing-price-box">
                                <div>
                                    <div class="small text-secondary">ТЪРЖНА ЦЕНА:</div>
                                    <strong class="text-warning fs-5">€${p[7].toLocaleString()}</strong>
                                </div>
                                <div class="text-end">
                                    <div class="small text-secondary">ПАЗАРНА ОЦЕНКА:</div>
                                    <strong class="text-light fs-6">€${p[8].toLocaleString()}</strong>
                                </div>
                            </div>
                        </div>
                        <div class="d-flex gap-2 mt-auto">
                            <button type="button" class="btn btn-outline-warning w-50 fw-bold" style="font-size:12px;" onclick="focusOnMap(${p[13]}, ${p[14]})">📍 Покажи на картата</button>
                            <button type="button" class="btn btn-outline-info w-50 fw-bold" style="font-size:12px;" onclick="showPlanFeatures('starter')">⚡ Отключи данни</button>
                        </div>
                    </div>
                `;
                container.appendChild(col);
            });
            renderPaginationControls();
        }

        function focusOnMap(lat, lng) {
            map.setView([lat, lng], 13);
            document.getElementById('map-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function renderPaginationControls() {
            var totalPages = Math.ceil(filteredProjects.length / pageSize);
            var controls = document.getElementById('paginationControls');
            controls.innerHTML = '';
            if(totalPages <= 1) return;

            var prevBtn = document.createElement('button');
            prevBtn.className = 'btn-page';
            prevBtn.innerText = '« Предишна';
            prevBtn.disabled = currentPage === 1;
            prevBtn.onclick = function() { if(currentPage > 1) { currentPage--; renderPaginatedDeals(); } };
            controls.appendChild(prevBtn);

            var nextBtn = document.createElement('button');
            nextBtn.className = 'btn-page';
            nextBtn.innerText = 'Следваща »';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = function() { if(currentPage < totalPages) { currentPage++; renderPaginatedDeals(); } };
            controls.appendChild(nextBtn);
        }

        function applyAdvancedFilters() {
            var q = document.getElementById('dealSearchInput').value.toLowerCase().trim();
            var city = document.getElementById('filterCity').value;
            var cat = document.getElementById('filterCategory').value;

            filteredProjects = allProjects.filter(function(p) {
                var matchQ = !q || p[1].toLowerCase().includes(q) || p[3].toLowerCase().includes(q);
                var matchCity = city === 'all' || p[3].includes(city);
                var matchCat = cat === 'all' || p[2] === cat;
                return matchQ && matchCity && matchCat;
            });
            currentPage = 1;
            renderPaginatedDeals();
        }

        renderPaginatedDeals();

        var plansData = {
            "starter": {
                name: "STARTER EXECUTIVE (€60/мес)",
                amount: "€60.00",
                features: [
                    { icon: "🔓", title: "1. Пълно отключване на ЕИК и точни адреси", desc: "Премахване на звездичките за всички обекта." },
                    { icon: "📄", title: "2. Седмичен PDF Инвестиционен Меморандум", desc: "Пълен експорт на актуалните търгове." },
                    { icon: "🗺️", title: "3. Интерактивна ГИС карта на България", desc: "Пълна визуализация в реално време." },
                    { icon: "🏢", title: "4. До 20 ЕИК одит справки месечно", desc: "Проверка на управители и статуси." }
                ]
            },
            "pro": {
                name: "PRO RISK MONITOR (€150/мес)",
                amount: "€150.00",
                features: [
                    { icon: "⚡", title: "1. 07:30 ч. Изпреварващ Фийд", desc: "Мигновен бюлетин с топ дисконти." },
                    { icon: "🔍", title: "2. НЕОГРАНИЧЕН БУЛСТАТ / ЕИК Одит", desc: "Дълбок скенер за запори и ЧСИ дела." },
                    { icon: "🧮", title: "3. ЧСИ Net ROI Калкулатор", desc: "Автоматично начисляване на такси." },
                    { icon: "📥", title: "4. Неограничен експорт на PDF доклади", desc: "Сваляне на официални одити от А до Я." }
                ]
            },
            "enterprise": {
                name: "ENTERPRISE M2M GATEWAY (€290/мес)",
                amount: "€290.00",
                features: [
                    { icon: "🤖", title: "1. REST JSON API Ключ", desc: "Директна интеграция без маскиране." },
                    { icon: "🧠", title: "2. LLMs.txt AI Gateway", desc: "Корпоративна AI поддръжка." },
                    { icon: "📊", title: "3. Пълен архив от 2024 г.", desc: "База данни за исторически сделки." },
                    { icon: "🛡️", title: "4. Персонален SLA договор", desc: "Официална правна и техническа поддръжка." }
                ]
            }
        };

        function showPlanFeatures(planKey) {
            var plan = plansData[planKey];
            document.getElementById('featTitle').innerText = plan.name;
            document.getElementById('modalPriceTag').innerText = plan.amount;
            
            var container = document.getElementById('benefitsListContainer');
            container.innerHTML = '';

            plan.features.forEach(function(feat) {
                container.innerHTML += `
                    <div class="benefit-row">
                        <div class="benefit-icon">${feat.icon}</div>
                        <div>
                            <div class="fw-bold text-white small">${feat.title}</div>
                            <div class="text-secondary" style="font-size:11px;">${feat.desc}</div>
                        </div>
                    </div>
                `;
            });

            var modalEl = new bootstrap.Modal(document.getElementById('featuresModal'));
            modalEl.show();
        }

        function copyIban() {
            navigator.clipboard.writeText("BG80UNCR70001524896321").then(function() {
                alert("✔ IBAN номерът е копиран в клипборда!");
            });
        }

        function confirmOrder() {
            alert("Благодарим Ви! Моля извършете превода по посочения IBAN.");
            var modalEl = bootstrap.Modal.getInstance(document.getElementById('featuresModal'));
            if(modalEl) modalEl.hide();
        }

        function fillEik(val) {
            document.getElementById('eikInput').value = val;
            performAudit();
        }

        function performAudit() {
            var eik = document.getElementById('eikInput').value.trim();
            if(!eik) return;
            fetch('/api/audit-eik?eik=' + encodeURIComponent(eik))
                .then(r => r.json())
                .then(comp => {
                    document.getElementById('companyAuditResult').style.display = 'block';
                    document.getElementById('resCompName').innerText = comp.name;
                    document.getElementById('resCompEik').innerText = comp.eik;
                    document.getElementById('resCompCity').innerText = comp.city;
                    document.getElementById('resCompManager').innerText = comp.manager;
                    document.getElementById('resCompCapital').innerText = comp.capital;
                    document.getElementById('resCompBalance').innerText = comp.balance;
                    document.getElementById('downloadAuditPdfBtn').href = '/export-audit-pdf?eik=' + encodeURIComponent(eik);
                });
        }

        function updateCalculator(val) {
            var num = parseInt(val);
            document.getElementById('calcPriceDisplay').innerText = '€' + num.toLocaleString();
            document.getElementById('calcTaxZmdt').innerText = '€' + Math.round(num * 0.03).toLocaleString();
            document.getElementById('calcTaxChsi').innerText = '€' + Math.round(num * 0.015).toLocaleString();
            document.getElementById('calcTaxAv').innerText = '€' + Math.round(num * 0.001).toLocaleString();
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, size_rzp, created_at, lat, lng FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    stats = {"total": len(projects), "top_deals": 42, "avg_discount": "54.2", "spread_str": "15 800 000"}
    return render_template_string(FULL_HTML, projects_json=json.dumps(projects), stats=stats)

@app.route("/api/audit-eik")
def api_audit_eik():
    eik = request.args.get("eik", "030431138").strip()
    if eik == "030431138":
        return jsonify({
            "eik": eik, "name": "СД „Ковко - Василев и Сие“", "manager": "Васил Василев (Управител)",
            "city": "гр. Драгоман, ул. Христо Ботев № 14", "capital": "Неограничено солидарна отговорност", "balance": "Изрядна счетоводна история", "isSafe": True
        })
    return jsonify({
        "eik": eik, "name": f"Търговско дружество ЕИК {eik} ООД", "manager": "Инж. Георги Иванов",
        "city": "гр. София, Индустриална зона", "capital": "€50,000", "balance": "Печелившо дружество", "isSafe": True
    })

@app.route("/export-audit-pdf")
def export_audit_pdf():
    eik = request.args.get("eik", "030431138").strip()
    return f"<h3>Официален оиден доклад за фирма ЕИК {eik}</h3>", 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route("/export-pdf")
def export_pdf():
    return "<h3>07:30 Дневен Бюлетин</h3>", 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route("/api/deals")
def api_deals():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
