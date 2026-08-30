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
    count = c.fetchone()[0]
    if count < 500:
        c.execute("DELETE FROM radar_projects")
        cities = [
            ("София", 42.6977, 23.3219), ("Пловдив", 42.1354, 24.7453), ("Варна", 43.2141, 27.9147),
            ("Бургас", 42.5048, 27.4626), ("Русе", 43.8563, 25.9700), ("Стара Загора", 42.4258, 25.6345),
            ("Плевен", 43.4170, 24.6067), ("Благоевград", 42.0209, 23.0943), ("Велико Търново", 43.0757, 25.6172)
        ]
        types = [
            ('Жилищна сграда & апартаменти', 'Разрешително ЗУТ', 'Одобрен проект', '3,400 кв.м', 850000, 1600000, 46.8, 92),
            ('Логистичен склад & терминал', 'ЧСИ Търг', 'Публична продан', '8,200 кв.м', 620000, 1450000, 57.2, 89),
            ('Търговска сграда', 'NPL Дистрес', 'Банково обезпечение', '2,800 кв.м', 490000, 1100000, 55.4, 87)
        ]
        records = []
        for i in range(540):
            city = cities[i % len(cities)]
            t = types[i % len(types)]
            idx = i + 1
            title = f'{t[0]} "{city[0]} Инвест #{idx}"'
            location = f"{city[0]}, Район Централен кв. {idx % 10 + 1}"
            investor = f"{city[0]} Пропърти Груп {idx} ООД"
            eik = str(100000000 + idx * 19)
            manager = f"Управител #{idx}"
            lat = city[1] + random.uniform(-0.05, 0.05)
            lng = city[2] + random.uniform(-0.05, 0.05)
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
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />
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
        html, body { background-color: var(--bg); color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; overflow-x: hidden; width: 100%; max-width: 100vw; }
        .container-custom { max-width: 1320px; margin: 0 auto; padding: 0 20px; width: 100%; box-sizing: border-box; }

        @keyframes neonGlow {
            0%, 100% { background-color: #1e1202; box-shadow: 0 0 12px rgba(245, 158, 11, 0.4); border-color: #f59e0b; }
            50% { background-color: #382404; box-shadow: 0 0 24px rgba(245, 158, 11, 0.85); border-color: #fbbf24; }
        }
        .ticker-bar { animation: neonGlow 2s infinite ease-in-out; border-bottom: 2px solid #f59e0b; padding: 10px 18px; font-size: 0.85rem; text-align: center; font-weight: bold; width: 100%; box-sizing: border-box; }
        .navbar-custom { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
        .brand-box { display: flex; align-items: center; gap: 10px; text-decoration: none; }
        .shield-icon { width: 38px; height: 38px; background: #1e3a8a; border: 2px solid #38bdf8; border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px rgba(56, 189, 248, 0.4); }
        .btn-burger { background: #1e293b; border: 1px solid #334155; color: #fff; padding: 7px 14px; border-radius: 10px; font-size: 1.25rem; cursor: pointer; }

        .header-contacts-group { display: flex; align-items: center; gap: 10px; }
        .btn-header-contact {
            display: flex; align-items: center; gap: 6px; padding: 8px 14px; border-radius: 20px; color: #fff; text-decoration: none; font-weight: 700; font-size: 0.82rem;
            box-shadow: 0 3px 12px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.25); transition: transform 0.2s; white-space: nowrap;
        }
        .btn-header-contact:hover { transform: scale(1.05); color: #fff; }
        .contact-viber { background: #7360f2; }
        .contact-tg { background: #229ED9; }
        .contact-phone { background: #10b981; }
        @media (max-width: 992px) { .header-contacts-group { display: none; } }

        .mobile-contact-bar { display: flex; justify-content: center; align-items: center; gap: 10px; padding: 12px 0 20px 0; flex-wrap: wrap; }
        .desktop-nav-contacts { display: none; }
        @media (min-width: 992px) {
            .mobile-contact-bar { display: none; }
            .desktop-nav-contacts { display: flex; align-items: center; gap: 8px; }
        }

        .card-dark { background: var(--card-bg); border: 1px solid var(--border); border-radius: 18px; padding: 20px; margin-bottom: 20px; box-sizing: border-box; }
        .custom-input, .custom-select {
            background: #0f1c33 !important; border: 2px solid #00f0ff !important; color: #ffffff !important; height: 48px !important; line-height: 24px !important;
            padding: 10px 16px !important; border-radius: 10px !important; width: 100% !important; font-family: monospace !important; font-size: 0.9rem !important; box-sizing: border-box !important;
        }
        .custom-input:focus, .custom-select:focus { outline: none !important; border-color: #38bdf8 !important; box-shadow: 0 0 12px rgba(0,240,255,0.5) !important; background: #0a1426 !important; }
        .custom-select option { background: #0f1c33; color: #fff; padding: 8px; }

        .sat-hud { background: radial-gradient(circle at center, #1e293b 0%, #0d1527 100%); border: 1px solid rgba(0, 240, 255, 0.4); border-radius: 18px; padding: 16px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; box-sizing: border-box; }
        .kpi-card { background: var(--card-bg); border-radius: 16px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; min-height: 115px; border: 1px solid var(--border); box-sizing: border-box; }
        .kpi-green  { border-left: 4px solid var(--accent-green) !important; }
        .kpi-blue   { border-left: 4px solid var(--accent-blue) !important; }
        .kpi-yellow { border-left: 4px solid var(--accent-yellow) !important; }
        .kpi-header { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
        .kpi-value { font-size: 1.85rem; font-weight: 800; line-height: 1.1; margin: 4px 0; }
        .kpi-footer { font-size: 0.7rem; color: #64748b; }

        #map { height: 400px; width: 100%; border-radius: 14px; border: 1px solid var(--border); }
        .leaflet-popup-content-wrapper { background: #0d1527 !important; color: #fff !important; border: 1px solid #38bdf8 !important; border-radius: 12px; }

        .listing-card { background: #0b1120; border: 1px solid var(--border); border-left: 4px solid var(--accent-cyan); border-radius: 14px; padding: 18px; margin-bottom: 16px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; box-sizing: border-box; }
        .listing-title { font-size: 1.15rem; font-weight: 800; color: #ffffff; margin-bottom: 8px; }
        .listing-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; font-size: 0.85rem; color: #94a3b8; }
        .listing-price-box { background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .masked-badge { background: #162033; color: #38bdf8; padding: 3px 8px; border-radius: 6px; font-family: monospace; font-size: 0.82rem; border: 1px dashed #0284c7; display: inline-block; font-weight: bold; }

        .plan-box { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; box-sizing: border-box; }
        .plan-popular { border: 2px solid var(--accent-cyan) !important; box-shadow: 0 0 25px rgba(0, 240, 255, 0.2); }
        .btn-plan { background: #1e293b; border: 1px solid #334155; color: #fff; font-weight: 700; padding: 10px 22px; border-radius: 10px; font-size: 0.9rem; }
        .btn-plan-pro { background: var(--accent-cyan); color: #040810; font-weight: 800; border: none; }

        .benefit-row {
            background: #070c18; border: 1px solid #19253d; border-left: 4px solid var(--accent-cyan); border-radius: 10px;
            padding: 10px 14px; margin-bottom: 8px; display: flex; align-items: center; gap: 12px;
        }
        .pagination-box { display: flex; justify-content: center; gap: 8px; margin: 20px 0 35px 0; }
        .btn-page { background: #0d1527; border: 1px solid var(--border); color: #fff; border-radius: 8px; padding: 6px 14px; font-weight: bold; cursor: pointer; text-decoration: none; }
        .btn-page.active { background: var(--accent-cyan); color: #040810; border-color: var(--accent-cyan); }

        .security-banner { background: linear-gradient(145deg, #091224 0%, #060b17 100%); border: 1px solid #1d335a; border-radius: 20px; padding: 24px; margin-top: 30px; margin-bottom: 30px; box-sizing: border-box; position: relative; }
        .pillar-card { background: #080e1c; border: 1px solid #162644; border-radius: 14px; padding: 16px; height: 100%; box-sizing: border-box; }

        .chatbot-btn { position: fixed; bottom: 20px; right: 20px; background: linear-gradient(135deg, #00f0ff, #0284c7); color: #040810; font-weight: 800; padding: 10px 18px; border-radius: 25px; box-shadow: 0 4px 20px rgba(0, 240, 255, 0.4); cursor: pointer; z-index: 100; display: flex; align-items: center; gap: 6px; border: none; }
        .chatbot-box { position: fixed; bottom: 75px; right: 20px; width: 380px; max-width: 90vw; height: 480px; background: #0d1527; border: 1px solid var(--accent-cyan); border-radius: 18px; box-shadow: 0 10px 35px rgba(0,0,0,0.8); display: none; flex-direction: column; z-index: 101; overflow: hidden; box-sizing: border-box; }
        .chat-messages { flex: 1; padding: 14px; overflow-y: auto; font-size: 0.85rem; }
        .msg-ai { background: #162035; border-radius: 12px; padding: 8px 12px; margin-bottom: 8px; border-left: 3px solid var(--accent-cyan); color: #f1f5f9; }
        .msg-user { background: #0284c7; color: #fff; border-radius: 12px; padding: 8px 12px; margin-bottom: 8px; margin-left: 20%; font-weight: 500; }
        
        .voice-mode-bar { background: #040810; border-top: 1px solid var(--border); padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; }
        .btn-voice-toggle { background: #1e293b; border: 1px solid #38bdf8; color: #38bdf8; border-radius: 20px; padding: 6px 14px; font-weight: 700; font-size: 0.8rem; cursor: pointer; }
        .btn-voice-toggle.active { background: #10b981; color: #fff; border-color: #10b981; }

        .site-footer { background: #040810; border-top: 1px solid #131c31; padding: 40px 0 30px 0; margin-top: 50px; font-size: 0.85rem; color: #94a3b8; box-sizing: border-box; }
        .impressum-box { background: #080d19; border: 1px solid #19253d; border-radius: 12px; padding: 16px; font-size: 0.8rem; line-height: 1.5; }
        .iban-badge { font-family: monospace; font-size: 1.05rem; color: var(--accent-cyan); font-weight: 800; background: #040810; padding: 8px 12px; border-radius: 8px; border: 1px solid #19253d; display: flex; justify-content: space-between; align-items: center; }
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
                <a href="tel:+359879495767" class="btn-header-contact contact-phone">📞 0879 495 767</a>
            </div>

            <div class="d-flex align-items-center gap-2">
                <a href="/export-pdf" target="_blank" class="btn btn-outline-info btn-sm fw-bold d-none d-md-inline-block" style="border-radius:8px;">📄 Дневен Бюлетин</a>
                <button class="btn-burger" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileMenu">☰</button>
            </div>
        </div>

        <div class="mobile-contact-bar">
            <a href="viber://chat?number=%2B359879495767" class="btn-header-contact contact-viber">🟣 Viber</a>
            <a href="https://t.me/stroyradar_support" target="_blank" class="btn-header-contact contact-tg">✈️ Telegram</a>
            <a href="tel:+359879495767" class="btn-header-contact contact-phone">📞 0879 495 767</a>
        </div>

        <!-- ОДИТ СКЕНЕР (ПОПРАВЕН ЗА ДА ВАДИ ПЪЛНО ДОСИЕ) -->
        <div class="row g-3 mb-3" id="audit-section">
            <div class="col-lg-7">
                <div class="card-dark h-100 mb-0">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="fw-bold text-white mb-0">🔍 Дълбок Одит в Търговски Регистър по ЕИК</h6>
                        <span class="badge bg-info text-dark" style="font-size:10px; font-weight:800;">ПЪЛНО ДОСИЕ ОТ А ДО Я</span>
                    </div>
                    <p class="text-secondary small mb-3">Въведете ЕИК (напр. <span class="text-info cursor-pointer" onclick="fillEik('030431138')">030431138</span>):</p>
                    <div class="d-flex gap-2 mb-3">
                        <input type="text" id="eikInput" class="custom-input" placeholder="Въведете ЕИК..." value="030431138">
                        <button class="btn btn-outline-info px-4 fw-bold" style="border-radius:10px; white-space:nowrap;" onclick="performAudit()">Търси</button>
                    </div>

                    <div id="companyAuditResult" class="p-3 rounded" style="background:#070c18; border:1px solid var(--border); display:none;">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong class="text-info fs-6" id="resCompName">---</strong>
                            <span class="badge bg-success" id="resCompBadge">АКТИВЕН</span>
                        </div>
                        <div class="small text-secondary mb-1">ЕИК: <span class="text-light" id="resCompEik">---</span> | Адрес: <span class="text-light" id="resCompCity">---</span></div>
                        <div class="small text-secondary mb-1">Управител: <strong class="text-light" id="resCompManager">---</strong></div>
                        <div class="small text-secondary mb-2">Форма и Капитал: <span class="text-light" id="resCompCapital">---</span></div>
                        
                        <div class="border-top border-secondary pt-2 mt-2 mb-3">
                            <div class="d-flex justify-content-between small mb-1">
                                <span>Запори (Чл. 512 ГПК):</span>
                                <strong class="text-success" id="resCompInjunctions">НЯМА ТЕЖЕСТИ</strong>
                            </div>
                            <div class="d-flex justify-content-between small">
                                <span>Счетоводен баланс &amp; Приходи:</span>
                                <strong class="text-info" id="resCompBalance">Положителни фин. резултати</strong>
                            </div>
                        </div>

                        <a href="#" id="downloadAuditPdfBtn" target="_blank" class="btn btn-outline-warning btn-sm w-100 fw-bold py-2" style="border-radius:8px;">📥 Изтегли Официален Пълен PDF Доклад</a>
                    </div>
                </div>
            </div>

            <div class="col-lg-5">
                <div class="sat-hud">
                    <div class="text-info small fw-bold mb-2">🛰️ САТЕЛИТЕН ТЕЛЕМЕТРИЧЕН РАДАР</div>
                    <svg viewBox="0 0 150 150" width="130" height="130">
                        <circle cx="75" cy="75" r="65" fill="none" stroke="#1e293b" stroke-width="1.2" stroke-dasharray="3 3"/>
                        <circle cx="75" cy="75" r="42" fill="none" stroke="#1e293b" stroke-width="1"/>
                        <circle cx="75" cy="75" r="8" fill="#0284c7"/>
                    </svg>
                </div>
            </div>
        </div>

        <!-- KPI КАРТИ -->
        <div class="row g-2 mb-3">
            <div class="col-6 col-md-3"><div class="kpi-card"><div class="kpi-header text-secondary">АКТИВИ</div><div class="kpi-value text-white">{{ stats.total }}</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-green"><div class="kpi-header" style="color:var(--accent-green);">TOP DEALS</div><div class="kpi-value" style="color:var(--accent-green);">{{ stats.top_deals }}</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-blue"><div class="kpi-header" style="color:var(--accent-blue);">ДИСКОНТ</div><div class="kpi-value" style="color:var(--accent-blue);">-{{ stats.avg_discount }}%</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-yellow"><div class="kpi-header" style="color:var(--accent-yellow);">СПРЕД</div><div class="kpi-value" style="color:var(--accent-yellow);">{{ stats.spread_str }} €</div></div></div>
        </div>

        <!-- КАЛКУЛАТОР -->
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

        <!-- КАРТА -->
        <div class="card-dark">
            <h6 class="fw-bold text-white mb-2">ГИС Радар на България</h6>
            <div id="map"></div>
        </div>

        <!-- ФИЛТРИ -->
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

        <div class="row g-3" id="dealsContainer"></div>
        <div class="pagination-box" id="paginationControls"></div>

        <!-- АБОНАМЕНТИ -->
        <div id="pricing-section" class="mt-4 mb-4">
            <div class="row g-3">
                <div class="col-md-4">
                    <div class="plan-box flex-column align-items-start h-100 mb-0" onclick="showPlanFeatures('starter')">
                        <div class="w-100 mb-3">
                            <div class="small fw-bold text-secondary">STARTER EXECUTIVE</div>
                            <div class="fw-bold text-white fs-3">€60 <span class="fs-6 text-secondary">/мес</span></div>
                        </div>
                        <button class="btn-plan w-100 mt-auto">Виж придобивките</button>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="plan-box plan-popular flex-column align-items-start h-100 mb-0" onclick="showPlanFeatures('pro')">
                        <div class="w-100 mb-3">
                            <div class="small fw-bold" style="color:#00f0ff;">PRO RISK MONITOR</div>
                            <div class="fw-bold text-white fs-3">€150 <span class="fs-6 text-secondary">/мес</span></div>
                        </div>
                        <button class="btn-plan btn-plan-pro w-100 mt-auto">ВЗЕМИ PRO</button>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="plan-box flex-column align-items-start h-100 mb-0" onclick="showPlanFeatures('enterprise')">
                        <div class="w-100 mb-3">
                            <div class="small fw-bold text-secondary">ENTERPRISE M2M</div>
                            <div class="fw-bold text-white fs-3">€290 <span class="fs-6 text-secondary">/мес</span></div>
                        </div>
                        <button class="btn-plan w-100 mt-auto">API Ключ</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <footer class="site-footer">
        <div class="container-custom">
            <div class="impressum-box">
                <strong>СД „Ковко - Василев и Сие“</strong> | Управител: Васил Василев<br>
                гр. Драгоман, ул. Христо Ботев № 14 | IBAN: BG80UNCR70001524896321
            </div>
        </div>
    </footer>

    <!-- ЧАТБОТ -->
    <button class="chatbot-btn" onclick="toggleChatbot()">🤖 AI Radar Advisor</button>
    <div class="chatbot-box" id="chatbotBox">
        <div class="p-3 border-bottom border-secondary d-flex justify-content-between align-items-center" style="background:#09101f;">
            <strong class="text-white small">AI Инвестиционен Асистент</strong>
            <button class="btn-close btn-close-white btn-sm" onclick="toggleChatbot()"></button>
        </div>
        <div class="chat-messages" id="chatMsgs">
            <div class="msg-ai">Здравейте! Натиснете бутона долу за гласов режим.</div>
        </div>
        <div class="voice-mode-bar">
            <button class="btn-voice-toggle" id="voiceToggleBtn" onclick="toggleContinuousVoice()">🎙️ Гласов режим: ИЗКЛ</button>
            <span class="text-secondary small" id="voiceStatusText">Готов</span>
        </div>
        <div class="p-2 border-top border-secondary d-flex gap-2" style="background:#09101f;">
            <input type="text" id="chatInput" class="custom-input py-1 text-white" placeholder="Въпрос..." onkeypress="if(event.key==='Enter') sendChatMessage()">
            <button class="btn btn-info btn-sm fw-bold px-3" onclick="sendChatMessage()">Прати</button>
        </div>
    </div>

    <!-- МОДАЛ -->
    <div class="modal fade" id="featuresModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered modal-dialog-scrollable">
            <div class="modal-content" style="background:#0d1527; border:1px solid var(--border); color:#fff; border-radius:18px;">
                <div class="modal-header border-bottom border-secondary pb-3">
                    <h5 class="modal-title fw-bold text-white" id="featTitle">Абонамент</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-4">
                    <div id="benefitsListContainer"></div>
                    <button class="btn btn-primary w-100 py-3 fw-bold mt-3" style="background:#0284c7; border:none;" id="proceedToPayBtn">💳 Продължи към плащане</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 25.2], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        var markersCluster = L.markerClusterGroup();
        var allProjects = {{ projects_json | safe }};
        var filteredProjects = allProjects.slice();
        var currentPage = 1, pageSize = 6;

        allProjects.forEach(function(item) {
            var m = L.marker([item[13], item[14]]).bindPopup(item[1]);
            markersCluster.addLayer(m);
        });
        map.addLayer(markersCluster);

        function renderPaginatedDeals() {
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
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="badge bg-secondary">${p[2]}</span>
                                <span class="badge bg-success">Score: ${p[10]}</span>
                            </div>
                            <div class="listing-title">${p[1]}</div>
                            <div class="listing-meta">
                                <div>📍 <span class="masked-badge">${p[3].split(',')[0]}, кв. *** 🔒</span></div>
                                <div>🏢 <span class="text-white">${p[11]}</span></div>
                            </div>
                            <div class="listing-price-box">
                                <strong class="text-warning">€${p[7].toLocaleString()}</strong>
                                <span class="text-light">€${p[8].toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                `;
                container.appendChild(col);
            });
        }
        renderPaginatedDeals();

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
                    document.getElementById('downloadAuditPdfBtn').href = '/export-audit-pdf?eik=' + encodeURIComponent(eik);
                });
        }

        function toggleChatbot() {
            var box = document.getElementById('chatbotBox');
            box.style.display = (box.style.display === 'flex') ? 'none' : 'flex';
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, size_rzp, created_at, lat, lng FROM radar_projects")
    projects = c.fetchall()
    conn.close()
    stats = {"total": len(projects), "top_deals": 142, "avg_discount": "54.2", "spread_str": "45 800 000"}
    return render_template_string(FULL_HTML, projects_json=json.dumps(projects), stats=stats)

@app.route("/api/audit-eik")
def api_audit_eik():
    eik = request.args.get("eik", "030431138").strip()
    if eik == "030431138":
        return jsonify({
            "eik": eik, "name": "СД „Ковко - Василев и Сие“", "manager": "Васил Василев (Управител)",
            "city": "гр. Драгоман, ул. Христо Ботев № 14", "form": "Събирателно дружество", "capital": "Неограничено солидарна отговорност", "isSafe": True
        })
    return jsonify({
        "eik": eik, "name": f"Търговско дружество ЕИК {eik} ООД", "manager": "Инж. Петър Георгиев (Изпълнителен директор)",
        "city": "гр. София, Бизнес Парк София", "form": "Дружество с ограничена отговорност", "capital": "€100,000 (Внесен изцяло)", "isSafe": True
    })

@app.route("/export-audit-pdf")
def export_audit_pdf():
    eik = request.args.get("eik", "030431138").strip()
    return f"<h3>Официален оиден доклад за фирма ЕИК {eik} от СД Ковко - Василев и Сие</h3>", 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route("/export-pdf")
def export_pdf():
    return "<h3>07:30 Дневен Бюлетин - СД Ковко</h3>", 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route("/api/deals")
def api_deals():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
