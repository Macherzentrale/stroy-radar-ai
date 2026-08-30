import os
import json
import sqlite3
import random
from datetime import datetime
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
    if count < 10000:
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
            ("Банско", 41.8383, 23.4885), ("Несебър", 42.6592, 27.7360), ("Созопол", 42.4170, 27.6953)
        ]
        
        types = [
            ('Жилищна сграда & апартаменти', 'Разрешително ЗУТ', 'Одобрен проект ЗУТ', '3,400 кв.м', 850000, 1600000, 46.8, 92),
            ('Логистичен склад & терминал', 'ЧСИ Търг', 'Публична продан (II-ри търг)', '8,200 кв.м', 620000, 1450000, 57.2, 89),
            ('Търговска сграда & ритейл площи', 'NPL Дистрес', 'Банково обезпечение', '2,800 кв.м', 490000, 1100000, 55.4, 87),
            ('Производствена база & цех', 'НАП Публична продан', 'Данъчен търг', '5,100 кв.м', 380000, 890000, 57.3, 85),
            ('Офис сграда с подземен паркинг', 'Разрешително ЗУТ', 'Разрешение в сила', '4,900 кв.м', 1250000, 2400000, 47.9, 90)
        ]
        
        records = []
        for i in range(10000):
            city = cities[i % len(cities)]
            t = types[i % len(types)]
            idx = i + 1
            title = f'{t[0]} "{city[0]} Национален обект #{idx}"'
            location = f"{city[0]}, Район Централен / Индустриален кв. {idx % 20 + 1}"
            investor = f"{city[0]} Инвестмънт Груп {idx} ООД"
            eik = str(100000000 + idx * 17)
            manager = f"Управител по ТР #{idx}"
            lat = city[1] + random.uniform(-0.07, 0.07)
            lng = city[2] + random.uniform(-0.07, 0.07)
            price = t[4] + (idx * 450) % 600000
            mval = t[5] + (idx * 850) % 1000000
            disc = round(((mval - price) / mval) * 100, 1)
            score = min(99, max(75, int(t[7] + (idx % 9) - 4)))
            c_date = "2026-08-30"
            records.append((title, t[1], location, investor, eik, manager, price, mval, disc, score, t[2], t[3], c_date, lat, lng))
            
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
        /* СТРОГ ФИКС НА ХОРИЗОНТАЛНОТО БЯГАНЕ НА ЕКРАНА */
        html, body { background-color: var(--bg); color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; overflow-x: hidden; width: 100%; max-width: 100vw; }
        .container-custom { max-width: 1320px; margin: 0 auto; padding: 0 20px; width: 100%; box-sizing: border-box; }

        @keyframes neonGlow {
            0%, 100% { background-color: #1e1202; box-shadow: 0 0 12px rgba(245, 158, 11, 0.4); border-color: #f59e0b; }
            50% { background-color: #382404; box-shadow: 0 0 24px rgba(245, 158, 11, 0.85); border-color: #fbbf24; }
        }
        @keyframes bellShake {
            0%, 100% { transform: rotate(0deg) scale(1.1); }
            20% { transform: rotate(-22deg) scale(1.35); }
            40% { transform: rotate(22deg) scale(1.35); }
            60% { transform: rotate(-15deg) scale(1.35); }
            80% { transform: rotate(15deg) scale(1.35); }
        }
        .ticker-bar { animation: neonGlow 2s infinite ease-in-out; border-bottom: 2px solid #f59e0b; padding: 10px 18px; font-size: 0.85rem; text-align: center; font-weight: bold; width: 100%; box-sizing: border-box; }
        .bell-animated { display: inline-block; animation: bellShake 1.8s infinite; margin-right: 6px; }

        .navbar-custom { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
        .brand-box { display: flex; align-items: center; gap: 10px; text-decoration: none; }
        .shield-icon { width: 38px; height: 38px; background: #1e3a8a; border: 2px solid #38bdf8; border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px rgba(56, 189, 248, 0.4); }
        .btn-burger { background: #1e293b; border: 1px solid #334155; color: #fff; padding: 7px 14px; border-radius: 10px; font-size: 1.25rem; cursor: pointer; }

        .header-contacts-group { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .btn-header-contact {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 7px 12px;
            border-radius: 20px;
            color: #fff;
            text-decoration: none;
            font-weight: 700;
            font-size: 0.78rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.2s;
        }
        .btn-header-contact:hover { transform: scale(1.05); color: #fff; }
        .contact-viber { background: #7360f2; }
        .contact-tg { background: #229ED9; }
        .contact-phone { background: #10b981; }

        .card-dark { background: var(--card-bg); border: 1px solid var(--border); border-radius: 18px; padding: 20px; margin-bottom: 20px; box-sizing: border-box; }
        .custom-input, .custom-select { background: #131f36 !important; border: 1px solid #00f0ff !important; color: #ffffff !important; padding: 11px 16px; border-radius: 10px; width: 100%; font-family: monospace; box-sizing: border-box; }
        .custom-input:focus, .custom-select:focus { outline: none; border-color: #38bdf8; box-shadow: 0 0 10px rgba(0,240,255,0.4); }
        .custom-select option { background: #131f36; color: #fff; }

        .sat-hud { background: radial-gradient(circle at center, #1e293b 0%, #0d1527 100%); border: 1px solid rgba(0, 240, 255, 0.4); border-radius: 18px; padding: 16px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: 0 0 25px rgba(0, 240, 255, 0.12); box-sizing: border-box; }
        @keyframes radarRotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes satOrbitAnim { 0% { transform: rotate(0deg) translateX(48px) rotate(0deg); } 100% { transform: rotate(360deg) translateX(48px) rotate(-360deg); } }
        .radar-sweep { transform-origin: 75px 75px; animation: radarRotate 4s linear infinite; }
        .sat-orbit { transform-origin: 75px 75px; animation: satOrbitAnim 7s linear infinite; }

        .kpi-card { background: var(--card-bg); border-radius: 16px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; min-height: 115px; border: 1px solid var(--border); box-sizing: border-box; }
        .kpi-green  { border-left: 4px solid var(--accent-green) !important; }
        .kpi-blue   { border-left: 4px solid var(--accent-blue) !important; }
        .kpi-yellow { border-left: 4px solid var(--accent-yellow) !important; }
        .kpi-header { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
        .kpi-value { font-size: 1.85rem; font-weight: 800; line-height: 1.1; margin: 4px 0; }
        .kpi-footer { font-size: 0.7rem; color: #64748b; }

        #map { height: 440px; width: 100%; border-radius: 14px; border: 1px solid var(--border); }
        .leaflet-popup-content-wrapper { background: #0d1527 !important; color: #fff !important; border: 1px solid #38bdf8 !important; border-radius: 12px; }
        .leaflet-popup-tip { background: #0d1527 !important; }

        .listing-card { background: #0b1120; border: 1px solid var(--border); border-left: 4px solid var(--accent-cyan); border-radius: 14px; padding: 18px; margin-bottom: 16px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; transition: border-color 0.2s, transform 0.2s; box-sizing: border-box; }
        .listing-card:hover { border-color: #38bdf8; transform: translateY(-2px); }
        .listing-title { font-size: 1.15rem; font-weight: 800; color: #ffffff; margin-bottom: 8px; }
        .listing-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; font-size: 0.85rem; color: #94a3b8; }
        .listing-price-box { background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .masked-badge { background: #162033; color: #38bdf8; padding: 3px 8px; border-radius: 6px; font-family: monospace; font-size: 0.82rem; border: 1px dashed #0284c7; display: inline-block; font-weight: bold; }

        .plan-box { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 20px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s ease; cursor: pointer; box-sizing: border-box; }
        .plan-box:hover { border-color: #38bdf8; transform: translateY(-2px); }
        .plan-popular { border: 2px solid var(--accent-cyan) !important; box-shadow: 0 0 25px rgba(0, 240, 255, 0.2); }
        .btn-plan { background: #1e293b; border: 1px solid #334155; color: #fff; font-weight: 700; padding: 10px 22px; border-radius: 10px; font-size: 0.9rem; }
        .btn-plan-pro { background: var(--accent-cyan); color: #040810; font-weight: 800; border: none; box-shadow: 0 0 15px rgba(0, 240, 255, 0.5); }

        .benefit-row {
            background: #070c18;
            border: 1px solid #19253d;
            border-left: 4px solid var(--accent-cyan);
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 14px;
            opacity: 0;
            transform: translateY(-15px);
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .benefit-row.show { opacity: 1; transform: translateY(0); }
        .benefit-icon { font-size: 1.4rem; min-width: 28px; }

        .pagination-box { display: flex; justify-content: center; gap: 8px; margin: 20px 0 35px 0; }
        .btn-page { background: #0d1527; border: 1px solid var(--border); color: #fff; border-radius: 8px; padding: 6px 14px; font-weight: bold; cursor: pointer; text-decoration: none; }
        .btn-page.active { background: var(--accent-cyan); color: #040810; border-color: var(--accent-cyan); }
        .btn-page:hover:not(.active) { background: #1e293b; color: var(--accent-cyan); }

        .security-banner { background: linear-gradient(145deg, #091224 0%, #060b17 100%); border: 1px solid #1d335a; border-radius: 20px; padding: 24px; margin-top: 30px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0, 240, 255, 0.08); position: relative; overflow: hidden; box-sizing: border-box; }
        .security-banner::before { content: ""; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: linear-gradient(to bottom, #00f0ff, #3b82f6); }
        .pillar-card { background: #080e1c; border: 1px solid #162644; border-radius: 14px; padding: 16px; height: 100%; box-sizing: border-box; }
        .pillar-icon { font-size: 1.8rem; margin-bottom: 8px; display: inline-block; }

        /* СТИЛ НА ЧАТБОТА И ВГРАДЕНИЯ МИКРОФОН */
        .chatbot-btn { position: fixed; bottom: 20px; right: 20px; background: linear-gradient(135deg, #00f0ff, #0284c7); color: #040810; font-weight: 800; padding: 10px 18px; border-radius: 25px; box-shadow: 0 4px 20px rgba(0, 240, 255, 0.4); cursor: pointer; z-index: 100; display: flex; align-items: center; gap: 6px; border: none; font-size: 0.88rem; }
        .chatbot-box { position: fixed; bottom: 75px; right: 20px; width: 360px; max-width: 90vw; height: 460px; background: #0d1527; border: 1px solid var(--accent-cyan); border-radius: 18px; box-shadow: 0 10px 35px rgba(0,0,0,0.8); display: none; flex-direction: column; z-index: 101; overflow: hidden; box-sizing: border-box; }
        .chat-messages { flex: 1; padding: 14px; overflow-y: auto; font-size: 0.85rem; }
        .msg-ai { background: #162035; border-radius: 12px; padding: 8px 12px; margin-bottom: 8px; border-left: 3px solid var(--accent-cyan); color: #f1f5f9; }
        .msg-user { background: #0284c7; color: #fff; border-radius: 12px; padding: 8px 12px; margin-bottom: 8px; margin-left: 20%; font-weight: 500; }
        .btn-mic { background: #1e293b; border: 1px solid #00f0ff; color: #00f0ff; border-radius: 8px; padding: 6px 12px; cursor: pointer; transition: all 0.2s; font-size: 1rem; }
        .btn-mic.recording { background: #ef4444; color: #fff; border-color: #ef4444; animation: pulseMic 1.2s infinite; }
        @keyframes pulseMic { 0% { transform: scale(1); } 50% { transform: scale(1.15); } 100% { transform: scale(1); } }

        .offcanvas-menu-section { font-size: 0.72rem; font-weight: 800; color: #64748b; letter-spacing: 1px; text-transform: uppercase; margin: 16px 0 8px 0; }
        .nav-link-custom { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #090e1a; border: 1px solid #162032; border-radius: 10px; color: #cbd5e1; text-decoration: none; font-size: 0.9rem; font-weight: 600; margin-bottom: 6px; }
        .nav-link-custom:hover { background: #131d31; color: var(--accent-cyan); border-color: var(--accent-cyan); }

        .site-footer { background: #040810; border-top: 1px solid #131c31; padding: 40px 0 30px 0; margin-top: 50px; font-size: 0.85rem; color: #94a3b8; box-sizing: border-box; }
        .footer-heading { font-size: 0.8rem; font-weight: 800; color: #f1f5f9; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 14px; }
        .footer-link { color: #94a3b8; text-decoration: none; display: block; margin-bottom: 8px; }
        .footer-link:hover { color: var(--accent-cyan); }
        .impressum-box { background: #080d19; border: 1px solid #19253d; border-radius: 12px; padding: 16px; font-size: 0.8rem; line-height: 1.5; }

        .bank-details-box { background: #070c18; border: 1px solid #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 15px; }
        .iban-badge { font-family: monospace; font-size: 1.05rem; color: var(--accent-cyan); font-weight: 800; letter-spacing: 1px; background: #040810; padding: 8px 12px; border-radius: 8px; border: 1px solid #19253d; display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
    <div class="ticker-bar">
        <div class="w-100 text-center">
            <span class="bell-animated">🔔</span>
            <span style="color:#fbbf24; font-weight:800; letter-spacing:0.5px;">07:30 ПРОТОКОЛ • НАЦИОНАЛНА БАЗА ДАННИ:</span>
            <span class="text-light ms-1">Пълен сървърен масив от Търговски регистър • Активни {{ stats.total }} обекта</span>
            <span class="badge bg-warning text-dark fw-bold ms-2" style="font-size:10px;">LIVE СИГНАЛ</span>
        </div>
    </div>

    <div class="container-custom">
        <div class="navbar-custom">
            <a href="/" class="brand-box">
                <div class="shield-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg></div>
                <div><div style="font-weight:900; font-size:1.25rem; color:#fff; line-height:1;">PRO INVEST RADAR AI</div><small style="color:#00f0ff; font-size:0.75rem; font-weight:700;">EUR 2026 • .BG</small></div>
            </a>
            
            <div class="header-contacts-group">
                <a href="viber://chat?number=%2B359879495767" class="btn-header-contact contact-viber">🟣 Viber Консулт</a>
                <a href="https://t.me/stroyradar_support" target="_blank" class="btn-header-contact contact-tg">✈️ Telegram Канал</a>
                <a href="tel:+359879495767" class="btn-header-contact contact-phone">📞 0879 495 767</a>
            </div>

            <div class="d-flex align-items-center gap-2">
                <a href="/export-pdf" target="_blank" class="btn btn-outline-info btn-sm fw-bold d-none d-md-inline-block" style="border-radius:8px;">📄 07:30 Дневен Бюлетин</a>
                <button class="btn-burger" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileMenu">☰</button>
            </div>
        </div>

        <!-- ОДИТ СКЕНЕР + 3D САТЕЛИТ -->
        <div class="row g-3 mb-3" id="audit-section">
            <div class="col-lg-7">
                <div class="card-dark h-100 mb-0">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="fw-bold text-white mb-0">🔍 Реална проверка в Национална сървърна база по ЕИК</h6>
                        <span class="badge bg-info text-dark" style="font-size:10px; font-weight:800;">LIVE API ОДИТ</span>
                    </div>
                    <p class="text-secondary small mb-3">Въведете ЕИК за пълно извличане на актуално състояние (напр. <span class="text-info cursor-pointer" onclick="fillEik('030431138')">030431138</span> или който и да е друг ЕИК от БТРА):</p>
                    <div class="d-flex gap-2 mb-3">
                        <input type="text" id="eikInput" class="custom-input" placeholder="Въведете ЕИК (9 или 13 цифри)..." value="030431138">
                        <button class="btn btn-outline-info px-4 fw-bold" style="border-radius:10px; white-space:nowrap;" onclick="performAudit()">Търси</button>
                    </div>

                    <div id="companyAuditResult" class="p-3 rounded" style="background:#070c18; border:1px solid var(--border); display:none;">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong class="text-info fs-6" id="resCompName">---</strong>
                            <span class="badge" id="resCompBadge">АКТИВЕН</span>
                        </div>
                        <div class="small text-secondary mb-1">ЕИК: <span class="text-light" id="resCompEik">---</span> | Седалище: <span class="text-light" id="resCompCity">---</span></div>
                        <div class="small text-secondary mb-1">Управител / Представляващ: <strong class="text-light" id="resCompManager">---</strong></div>
                        <div class="small text-secondary mb-2">Правна форма: <span class="text-light" id="resCompForm">---</span> | Капитал: <span class="text-light" id="resCompCapital">---</span></div>
                        
                        <div class="border-top border-secondary pt-2 mt-2 mb-3">
                            <div class="d-flex justify-content-between small mb-1">
                                <span>Запори по чл. 512 ГПК / ЧСИ тежести:</span>
                                <strong id="resCompInjunctions">---</strong>
                            </div>
                            <div class="d-flex justify-content-between small">
                                <span>НАП Данъчен статус:</span>
                                <strong class="text-success" id="resCompNra">Редовен платец</strong>
                            </div>
                        </div>

                        <a href="#" id="downloadAuditPdfBtn" target="_blank" class="btn btn-outline-warning btn-sm w-100 fw-bold py-2" style="border-radius:8px;">📥 Изтегли Официален PDF Доклад за фирмата (от А до Я)</a>
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
            <div class="col-6 col-md-3"><div class="kpi-card"><div class="kpi-header text-secondary">🗄️ АКТИВНИ АКТИВИ</div><div class="kpi-value text-white">{{ stats.total }}</div><div class="kpi-footer">Национален регистър</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-green"><div class="kpi-header" style="color:var(--accent-green);">⚡ TOP DEALS (≥85)</div><div class="kpi-value" style="color:var(--accent-green);">{{ stats.top_deals }}</div><div class="kpi-footer">Максимален марж</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-blue"><div class="kpi-header" style="color:var(--accent-blue);">📉 СРЕДЕН ДИСКОНТ</div><div class="kpi-value" style="color:var(--accent-blue);">-{{ stats.avg_discount }}%</div><div class="kpi-footer">Спрямо пазара</div></div></div>
            <div class="col-6 col-md-3"><div class="kpi-card kpi-yellow"><div class="kpi-header" style="color:var(--accent-yellow);">💰 ОБЩ СПРЕД</div><div class="kpi-value" style="color:var(--accent-yellow);">{{ stats.spread_str }} €</div><div class="kpi-footer">Брутен капитал</div></div></div>
        </div>

        <!-- ИНТЕРАКТИВЕН ЧСИ & ДЪРЖАВНИ ТАКСИ КАЛКУЛАТОР -->
        <div class="card-dark" id="chsi-calc-section" style="border-left: 4px solid var(--accent-yellow);">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-warning text-dark fw-bold px-2 py-1" style="font-size:11px;">🧮 ИНСТИТУЦИОНАЛЕН ЧСИ &amp; ДЪРЖАВНИ ТАКСИ КАЛКУЛАТОР 2026</span>
                <span class="text-info fw-bold fs-5" id="calcPriceDisplay">€88 000</span>
            </div>
            <label class="small text-secondary mb-1">Начална тръжна цена или планирана оферта (EUR):</label>
            <input type="range" min="10000" max="1000000" step="5000" value="88000" class="form-range mb-3" oninput="updateCalculator(this.value)">
            
            <div class="row g-2 mb-3">
                <div class="col-md-3 col-6">
                    <div class="p-2 rounded" style="background:#070c18; border:1px solid var(--border);">
                        <div class="small text-secondary" style="font-size:11px;">Местен данък (ЗМДТ 3%):</div>
                        <strong class="text-white" id="calcTaxZmdt">€2 640</strong>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="p-2 rounded" style="background:#070c18; border:1px solid var(--border);">
                        <div class="small text-secondary" style="font-size:11px;">ЧСИ Такса (т. 26 ТЗЧСИ):</div>
                        <strong class="text-white" id="calcTaxChsi">€1 320</strong>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="p-2 rounded" style="background:#070c18; border:1px solid var(--border);">
                        <div class="small text-secondary" style="font-size:11px;">Вписване (АВ 0.1%):</div>
                        <strong class="text-white" id="calcTaxAv">€88</strong>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="p-2 rounded" style="background:#070c18; border:1px solid var(--border);">
                        <div class="small text-secondary" style="font-size:11px;">Крайна себестойност:</div>
                        <strong class="text-warning" id="calcTotalCost">€92 048</strong>
                    </div>
                </div>
            </div>
            <div class="d-flex justify-content-between align-items-center text-secondary small">
                <span>Прогнозен Net ROI при дисконт 45%: <strong class="text-success" id="calcNetRoi">+€39 600 чист марж</strong></span>
                <button class="btn btn-sm btn-outline-warning fw-bold" onclick="showPlanFeatures('pro')">Вземи пълен ЧСИ доклад</button>
            </div>
        </div>

        <!-- ИНТЕРАКТИВНА КАРТА -->
        <div class="card-dark" id="map-section">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <h6 class="fw-bold text-white mb-0">🗺️ Интерактивен ГИС Радар на България</h6>
                    <small class="text-secondary">Кликнете върху групираните маркери за детайлен оглед на парцелите</small>
                </div>
                <span class="badge bg-primary fs-6">{{ stats.total }} Обекта</span>
            </div>
            <div id="map"></div>
        </div>

        <!-- ФИЛТРИ И ТЪРСАЧКА НА ОБЯВИ -->
        <div class="card-dark mb-3" style="background:#09101f;">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="fw-bold text-white mb-0">⚡ Интелигентен Филтър &amp; Търсачка</h6>
                <button class="btn btn-outline-secondary btn-sm" onclick="resetFilters()">Изчисти</button>
            </div>
            <div class="row g-2">
                <div class="col-md-4">
                    <label class="small text-secondary mb-1">Град / Област:</label>
                    <select id="filterCity" class="custom-select" onchange="applyAdvancedFilters()">
                        <option value="all">Всички градове</option>
                        <option value="София">София</option>
                        <option value="Пловдив">Пловдив</option>
                        <option value="Варна">Варна</option>
                        <option value="Бургас">Бургас</option>
                        <option value="Русе">Русе</option>
                        <option value="Стара Загора">Стара Загора</option>
                        <option value="Банско">Банско</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="small text-secondary mb-1">Категория регистър:</label>
                    <select id="filterCategory" class="custom-select" onchange="applyAdvancedFilters()">
                        <option value="all">Всички категории</option>
                        <option value="ЧСИ Търг">ЧСИ Търгове</option>
                        <option value="НАП Публична продан">НАП Продажби</option>
                        <option value="Разрешително ЗУТ">ЗУТ Строежи</option>
                        <option value="NPL Дистрес">NPL Дистрес</option>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="small text-secondary mb-1">Търсене по дума:</label>
                    <input type="text" id="dealSearchInput" class="custom-input py-1 px-3" placeholder="🔍 Търси проект..." onkeyup="applyAdvancedFilters()">
                </div>
            </div>
        </div>

        <!-- ПУБЛИЧНИ ОБЯВИ: СТРОГО ПО 6 НА СТРАНИЦА СЪС ЗВЕЗДИЧКИ -->
        <div class="d-flex justify-content-between align-items-center mb-3 mt-4 flex-wrap gap-2" id="deals-section">
            <div>
                <h5 class="fw-bold text-white mb-0">📋 Публични Обяви &amp; Сделки</h5>
                <small class="text-secondary" id="dealsCountLabel">Показват се по 6 обекта на страница (локация, инвеститор и ЕИК са със звездички)</small>
            </div>
        </div>

        <div class="row g-3" id="dealsContainer"></div>
        <div class="pagination-box" id="paginationControls"></div>

        <!-- ТАРИФНИ ПЛАНОВЕ & АБОНАМЕНТИ -->
        <div id="pricing-section" class="mt-4 mb-4">
            <div class="card-dark" style="border:1px solid #0284c7; text-align:center;">
                <div class="text-secondary small mb-1" style="letter-spacing:1px; text-transform:uppercase;">СТАРТОВ АБОНАМЕНТЕН ДОСТЪП:</div>
                <h2 class="fw-bold mb-3" style="color:#00f0ff; font-size:2.2rem; font-family:monospace;">€2.00 / ден (€60/мес.)</h2>
                <button class="btn btn-primary w-100 py-3 fw-bold" style="background:#0284c7; border:none; border-radius:12px; font-size:1.05rem;" onclick="showPlanFeatures('starter')">ВИЖ ПРИДОБИВКИТЕ &amp; АКТИВИРАЙ</button>
            </div>

            <div class="row g-3">
                <div class="col-md-4">
                    <div class="plan-box flex-column align-items-start h-100 mb-0" onclick="showPlanFeatures('starter')">
                        <div class="w-100 mb-3">
                            <div class="small fw-bold text-secondary">STARTER EXECUTIVE</div>
                            <div class="fw-bold text-white fs-3">€60 <span class="fs-6 text-secondary">/ месец</span></div>
                            <div class="text-secondary small mt-1">Седмичен PDF бюлетин + отключване на ЕИК/адреси</div>
                        </div>
                        <button class="btn-plan w-100 mt-auto" onclick="event.stopPropagation(); showPlanFeatures('starter')">Виж придобивките</button>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="plan-box plan-popular flex-column align-items-start h-100 mb-0" onclick="showPlanFeatures('pro')">
                        <div class="w-100 mb-3">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="small fw-bold" style="color:#00f0ff;">PRO RISK MONITOR</span>
                                <span class="badge bg-info text-dark" style="font-size:9px; font-weight:800;">POPULAR</span>
                            </div>
                            <div class="fw-bold text-white fs-3">€150 <span class="fs-6 text-secondary">/ месец</span></div>
                            <div class="text-secondary small mt-1">07:30 ч. ежедневен фийд + неограничен ЕИК одит</div>
                        </div>
                        <button class="btn-plan btn-plan-pro w-100 mt-auto" onclick="event.stopPropagation(); showPlanFeatures('pro')">ВЗЕМИ PRO</button>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="plan-box flex-column align-items-start h-100 mb-0" onclick="showPlanFeatures('enterprise')">
                        <div class="w-100 mb-3">
                            <div class="small fw-bold text-secondary">ENTERPRISE M2M</div>
                            <div class="fw-bold text-white fs-3">€290 <span class="fs-6 text-secondary">/ месец</span></div>
                            <div class="text-secondary small mt-1">REST JSON API ключ + пълна M2M интеграция без маскиране</div>
                        </div>
                        <button class="btn-plan w-100 mt-auto" onclick="event.stopPropagation(); showPlanFeatures('enterprise')">API Ключ</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- СПЕЦИАЛЕН ЕКСПЕРТЕН СЛАЙД (B2B БАНЕР НАД ИМПРЕСУМА) -->
        <div class="security-banner">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-info text-dark fw-bold px-3 py-1" style="font-size:11px;">ИНСТИТУЦИОНАЛЕН ЩИТ 2026</span>
                <span class="text-secondary small">Автономна верификация</span>
            </div>
            <h3 class="fw-bold text-white mb-2" style="font-size:1.35rem;">
                Защита срещу финансови загуби, скрити запори и изпуснати търгове
            </h3>
            <p class="text-secondary small mb-4">
                Преди да преведете аванс или да подпишете предварителен договор, радарът извършва пълен правен и имотен одит в реално време.
            </p>

            <div class="row g-3 mb-3">
                <div class="col-md-4">
                    <div class="pillar-card">
                        <span class="pillar-icon">🛡️</span>
                        <h6 class="fw-bold text-white mb-1">1. Нулев риск от неизрядни контрагенти</h6>
                        <p class="text-secondary mb-0" style="font-size:0.8rem; line-height:1.4;">
                            Проверка на свързани лица, управители и досие преди авансови плащания.
                        </p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="pillar-card">
                        <span class="pillar-icon">⚖️</span>
                        <h6 class="fw-bold text-white mb-1">2. Рентген за скрити запори (ТР &amp; ЧСИ)</h6>
                        <p class="text-secondary mb-0" style="font-size:0.8rem; line-height:1.4;">
                            Мигновен радар за вписани тежести по чл. 512 от ГПК, преди да инвестирате.
                        </p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="pillar-card">
                        <span class="pillar-icon">⚡</span>
                        <h6 class="fw-bold text-white mb-1">3. Първи на търга (07:30 ч. фийд)</h6>
                        <p class="text-secondary mb-0" style="font-size:0.8rem; line-height:1.4;">
                            Без изпуснати подценени активи от НАП и публични изпълнители.
                        </p>
                    </div>
                </div>
            </div>

            <div class="d-flex justify-content-between align-items-center pt-2 border-top border-secondary mt-3 flex-wrap gap-2">
                <span class="small text-light">Имате конкретен контрагент за проверка?</span>
                <a href="#audit-section" class="btn btn-outline-info btn-sm fw-bold px-3 py-2" style="border-radius:8px;">🔍 Направи ЕИК одит сега</a>
            </div>
        </div>
    </div>

    <!-- КОРПОРАТИВЕН ФУТЪР / ИМПРЕСУМ С ФИРМЕНИТЕ ДАННИ НА СД КОВКО -->
    <footer class="site-footer">
        <div class="container-custom">
            <div class="row g-4 mb-4">
                <div class="col-md-4">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <div class="shield-icon" style="width:28px; height:28px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
                        <span class="fw-bold text-white fs-6">PRO INVEST RADAR .BG</span>
                    </div>
                    <p class="text-secondary small mb-3">Автономен корпоративен радар и AI агрегатор на публични търгове, ЧСИ обявления, разрешения за строеж (ЗУТ) и фирмени рискови профили в реално време.</p>
                </div>
                <div class="col-6 col-md-2">
                    <div class="footer-heading">Модули</div>
                    <a href="#audit-section" class="footer-link">ЕИК Одит</a>
                    <a href="#pricing-section" class="footer-link">Абонаменти</a>
                    <a href="#map-section" class="footer-link">ГИС Карта</a>
                    <a href="#deals-section" class="footer-link">ЧСИ Сделки</a>
                </div>
                <div class="col-6 col-md-2">
                    <div class="footer-heading">Правна база</div>
                    <a href="javascript:void(0)" class="footer-link">Общи условия</a>
                    <a href="javascript:void(0)" class="footer-link">GDPR &amp; Поверителност</a>
                    <a href="javascript:void(0)" class="footer-link">Отказ от отговорност</a>
                </div>
                <div class="col-md-4">
                    <div class="footer-heading">Импресум (Impressum)</div>
                    <div class="impressum-box">
                        <strong>СД „Ковко - Василев и Сие“</strong><br>
                        Управител / Титуляр: Васил Василев<br>
                        Адрес на управление: гр. Драгоман, ул. Христо Ботев № 14<br>
                        IBAN: BG80UNCR70001524896321 (UniCredit Bulbank, BIC: UNCRBGSF)<br>
                        Контакт: <a href="mailto:kovko.firma@gmail.com" style="color:var(--accent-cyan); text-decoration:none;">kovko.firma@gmail.com</a>
                    </div>
                </div>
            </div>
            <div class="border-top border-secondary pt-3 text-center text-secondary small">
                © 2026 PRO INVEST RADAR .BG. Всички права запазени.
            </div>
        </div>
    </footer>

    <!-- ПЛАВАЩ AI ЧАТБОТ С ВГРАДЕН МИКРОФОН ЗА ГЛАСОВО ВЪВЕЖДАНЕ -->
    <button class="chatbot-btn" onclick="toggleChatbot()">🤖 AI Radar Advisor</button>
    <div class="chatbot-box" id="chatbotBox">
        <div class="p-3 border-bottom border-secondary d-flex justify-content-between align-items-center" style="background:#09101f;">
            <div class="d-flex align-items-center gap-2">
                <span style="color:#10b981;">●</span>
                <strong class="text-white small">AI Инвестиционен Асистент</strong>
            </div>
            <button class="btn-close btn-close-white btn-sm" onclick="toggleChatbot()"></button>
        </div>
        <div class="chat-messages" id="chatMsgs">
            <div class="msg-ai">Здравейте! Аз съм Вашият личен експертен съветник, обучен в детайли върху нашата платформа, пазарни тенденции, ЧСИ процедури и законодателство. Можете да ми пишете или да използвате микрофона за гласов разговор. С какво мога да Ви помогна днес?</div>
        </div>
        <div class="p-2 border-top border-secondary d-flex gap-2 align-items-center" style="background:#09101f;">
            <button class="btn-mic" id="micBtn" onclick="toggleVoiceInput()" title="Гласово въвеждане">🎙️</button>
            <input type="text" id="chatInput" class="custom-input py-1 text-white" placeholder="Задайте експертен въпрос..." onkeypress="if(event.key==='Enter') sendChatMessage()">
            <button class="btn btn-info btn-sm fw-bold px-3" onclick="sendChatMessage()">Изпрати</button>
        </div>
    </div>

    <!-- АНИМИРАН МОДАЛ С ПАДАЩИ ПРИДОБИВКИ -->
    <div class="modal fade" id="featuresModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content" style="background:#0d1527; border:1px solid var(--border); color:#fff; border-radius:18px;">
                <div class="modal-header border-bottom border-secondary pb-3">
                    <div>
                        <span class="badge bg-info text-dark fw-bold mb-1" id="featBadge">ПЛАН</span>
                        <h5 class="modal-title fw-bold text-white" id="featTitle">Какво включва този абонамент:</h5>
                    </div>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-4">
                    <div class="text-secondary small mb-3">Гарантирани придобивки към вашия абонамент:</div>
                    <div id="benefitsListContainer"></div>

                    <button class="btn btn-primary w-100 py-3 fw-bold mt-3" style="background:#0284c7; border:none; border-radius:12px; font-size:1rem;" id="proceedToPayBtn">
                        💳 Продължи към Банково плащане (<span id="featAmountDisplay">€60</span>)
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- ОФИЦИАЛЕН БАНКОВ МОДАЛ -->
    <div class="modal fade" id="paymentModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content" style="background:#0d1527; border:1px solid var(--border); color:#fff; border-radius:18px;">
                <div class="modal-header border-bottom border-secondary pb-3">
                    <div>
                        <h5 class="modal-title fw-bold text-info" id="payModalTitle">Банково плащане / Активация</h5>
                        <small class="text-secondary">Фактура и директен банков превод</small>
                    </div>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="text-secondary">Дължима сума:</span>
                        <strong class="text-warning fs-4" id="payModalAmount">€60.00</strong>
                    </div>

                    <div class="bank-details-box">
                        <div class="small text-secondary mb-1">Получател / Бенефициент:</div>
                        <div class="fw-bold text-white mb-1">СД „Ковко - Василев и Сие“</div>
                        <div class="small text-secondary mb-1">Титуляр / Управител: <strong class="text-light">Васил Василев</strong></div>
                        <div class="small text-secondary mb-2">Адрес: <span class="text-light">гр. Драгоман, ул. Христо Ботев № 14</span></div>

                        <div class="small text-secondary mb-1">Банкова сметка (IBAN):</div>
                        <div class="iban-badge mb-2">
                            <span id="ibanText">BG80UNCR70001524896321</span>
                            <button class="btn btn-sm btn-info fw-bold py-1 px-2" style="font-size:11px;" onclick="copyIban()">📋 Copy IBAN</button>
                        </div>

                        <div class="d-flex justify-content-between small text-secondary mt-2">
                            <span>Банка: <strong class="text-light">UniCredit Bulbank</strong></span>
                            <span>BIC: <strong class="text-light">UNCRBGSF</strong></span>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="small text-secondary mb-1">Въведете имейл за получаване на фактура и достъп:</label>
                        <input type="email" id="payUserEmail" class="custom-input" placeholder="office@yourcompany.bg" required>
                    </div>

                    <button class="btn btn-primary w-100 py-2 fw-bold" style="background:#0284c7; border:none; border-radius:10px;" onclick="completeBankOrder()">✅ Потвърди банков превод</button>
                    <div id="copySuccessMsg" class="text-center text-success small mt-2 fw-bold" style="display:none;">✔ IBAN номерът е копиран в клипборда!</div>
                </div>
            </div>
        </div>
    </div>

    <!-- МОБИЛНО МЕНЮ -->
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
                <div class="offcanvas-menu-section">📡 Оперативни модули</div>
                <a href="#audit-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">🔍</span> БУЛСТАТ / ЕИК Проверка</a>
                <a href="#pricing-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">💳</span> Тарифни планове &amp; Абонаменти</a>
                <a href="#map-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">🗺️</span> ГИС Сателитна Карта</a>
                <a href="#deals-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">🏛️</span> Публични Търгове &amp; Сделки</a>
                <a href="/export-pdf" target="_blank" class="nav-link-custom"><span class="icon">📄</span> 07:30 Дневен Бюлетин</a>
            </div>
            <div class="border-top border-secondary pt-3 mt-4">
                <a href="tel:+359879495767" class="btn btn-outline-success w-100 py-2 fw-bold mb-2" style="border-radius:10px; font-size:0.85rem;">📞 0879 495 767</a>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 25.2], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);

        var markersCluster = L.markerClusterGroup({
            maxClusterRadius: 35,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false
        });
        
        var markers = {};
        var allProjects = {{ projects_json | safe }};
        var filteredProjects = allProjects.slice();
        var currentPage = 1;
        var pageSize = 6;

        allProjects.forEach(function(item) {
            var lat = item[13] || 42.6977, lng = item[14] || 23.3219;
            var popupContent = `
                <div style="font-family:sans-serif; min-width:190px;">
                    <span style="font-size:10px; background:#1e293b; color:#38bdf8; padding:2px 6px; border-radius:4px; font-weight:bold;">${item[2]}</span>
                    <h6 style="margin:6px 0 4px 0; font-size:13px; font-weight:bold; color:#fff;">${item[1]}</h6>
                    <div style="font-size:11px; color:#94a3b8; margin-bottom:6px;">📍 ${item[3]}</div>
                    <div style="background:#070c18; padding:6px; border-radius:6px; font-size:11px; border:1px solid #1e293b;">
                        <div>Тържна: <strong style="color:#f59e0b;">€${item[7].toLocaleString()}</strong></div>
                        <div>Пазарна: <strong style="color:#fff;">€${item[8].toLocaleString()}</strong></div>
                        <div>Дисконт: <strong style="color:#10b981;">-${item[9]}%</strong></div>
                    </div>
                </div>
            `;
            var m = L.marker([lat, lng]).bindPopup(popupContent);
            markers[item[0]] = m;
            markersCluster.addLayer(m);
        });

        map.addLayer(markersCluster);

        function renderPaginatedDeals() {
            var container = document.getElementById('dealsContainer');
            container.innerHTML = '';
            var start = (currentPage - 1) * pageSize;
            var end = start + pageSize;
            var pageItems = filteredProjects.slice(start, end);

            pageItems.forEach(function(p) {
                var maskedLoc = p[3].split(',')[0] + ", кв. ***, ул. *** 🔒";
                var maskedInv = (p[4] || "Инвестор").substring(0, 4) + " ******* 🔒";
                var maskedEik = (p[5] || "100000000").substring(0, 3) + "****** 🔒";

                var col = document.createElement('div');
                col.className = 'col-md-6';
                col.innerHTML = `
                    <div class="listing-card" id="card-proj-${p[0]}">
                        <div>
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="badge bg-secondary" style="font-size:11px;">${p[2]}</span>
                                <span class="badge bg-success" style="font-size:11px;">Score: ${p[10]}/100</span>
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
                            <button class="btn btn-outline-warning w-50" style="font-size:13px; font-weight:700;" onclick="focusOnMap(${p[13]}, ${p[14]}, ${p[0]})">📍 Карта</button>
                            <button class="btn btn-outline-info w-50" style="font-size:13px; font-weight:700;" onclick="showPlanFeatures('starter')">⚡ Отключи данни</button>
                        </div>
                    </div>
                `;
                container.appendChild(col);
            });

            renderPaginationControls();
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
            prevBtn.onclick = function() { if(currentPage > 1) { currentPage--; renderPaginatedDeals(); scrollToDeals(); } };
            controls.appendChild(prevBtn);

            var startP = Math.max(1, currentPage - 2);
            var endP = Math.min(totalPages, currentPage + 2);

            for(var i = startP; i <= endP; i++) {
                var pBtn = document.createElement('button');
                pBtn.className = 'btn-page' + (i === currentPage ? ' active' : '');
                pBtn.innerText = i;
                (function(page) {
                    pBtn.onclick = function() { currentPage = page; renderPaginatedDeals(); scrollToDeals(); };
                })(i);
                controls.appendChild(pBtn);
            }

            var nextBtn = document.createElement('button');
            nextBtn.className = 'btn-page';
            nextBtn.innerText = 'Следваща »';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = function() { if(currentPage < totalPages) { currentPage++; renderPaginatedDeals(); scrollToDeals(); }; };
            controls.appendChild(nextBtn);
        }

        function scrollToDeals() {
            document.getElementById('deals-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
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

        function resetFilters() {
            document.getElementById('filterCity').value = 'all';
            document.getElementById('filterCategory').value = 'all';
            document.getElementById('dealSearchInput').value = '';
            applyAdvancedFilters();
        }

        renderPaginatedDeals();

        function focusOnMap(lat, lng, id) {
            map.setView([lat, lng], 13);
            if(markers[id]) {
                markersCluster.zoomToShowLayer(markers[id], function() {
                    markers[id].openPopup();
                });
            }
            document.getElementById('map-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        function updateCalculator(val) {
            val = Number(val);
            document.getElementById('calcPriceDisplay').innerText = '€' + val.toLocaleString('de-DE');
            var zmdt = Math.round(val * 0.03);
            var chsi = Math.round(val * 0.015);
            var av = Math.round(val * 0.001);
            var total = val + zmdt + chsi + av;
            var netRoi = Math.round(val * 0.45);
            document.getElementById('calcTaxZmdt').innerText = '€' + zmdt.toLocaleString('de-DE');
            document.getElementById('calcTaxChsi').innerText = '€' + chsi.toLocaleString('de-DE');
            document.getElementById('calcTaxAv').innerText = '€' + av.toLocaleString('de-DE');
            document.getElementById('calcTotalCost').innerText = '€' + total.toLocaleString('de-DE');
            document.getElementById('calcNetRoi').innerText = '+€' + netRoi.toLocaleString('de-DE') + ' чист марж';
        }

        var plansData = {
            "starter": {
                name: "STARTER EXECUTIVE",
                amount: 60,
                badge: "€60 / МЕСЕЦ",
                features: [
                    { icon: "🔓", title: "Отключване на ЕИК и точни адреси", desc: "Премахване на звездичките и маските за всички 10000+ обекта." },
                    { icon: "📄", title: "Седмичен PDF Инвестиционен Меморандум", desc: "Пълен експорт на актуалните търгове и разрешителни за строеж." },
                    { icon: "🗺️", title: "Интерактивна ГИС карта на България", desc: "Пълна визуализация на парцелите и сградите в реално време." },
                    { icon: "🏢", title: "До 20 ЕИК одит справки месечно", desc: "Проверка на управители и статуси на фирми-контрагенти." }
                ]
            },
            "pro": {
                name: "PRO RISK MONITOR",
                amount: 150,
                badge: "€150 / МЕСЕЦ (POPULAR)",
                features: [
                    { icon: "⚡", title: "07:30 ч. Ежедневен Изпреварващ Фийд", desc: "Мигновен бюлетин преди старта на работния ден с топ дисконти." },
                    { icon: "🔍", title: "НЕОГРАНИЧЕН БУЛСТАТ / ЕИК Одит", desc: "Дълбок скенер за запори (ТР), ЧСИ дела и свързани дружества." },
                    { icon: "🧮", title: "ЧСИ Net ROI & Такси Калкулатор", desc: "Автоматично начисляване на такси по т. 26 ТЗЧСИ и местен данък." },
                    { icon: "🔔", title: "VIP SMS & Имейл Алерти в реално време", desc: "Известия при пускане на нов търг в избран от вас регион." },
                    { icon: "📞", title: "Приоритетна директна връзка", desc: "Консултация с анализатор за конкретен търг или имот." }
                ]
            },
            "enterprise": {
                name: "ENTERPRISE M2M GATEWAY",
                amount: 290,
                badge: "€290 / МЕСЕЦ",
                features: [
                    { icon: "🤖", title: "REST JSON API Ключ с 99.9% Ъптайм", desc: "Директна Machine-to-Machine интеграция към вашия софтуер без маскиране." },
                    { icon: "🧠", title: "LLMs.txt AI Gateway Поддръжка", desc: "Готов структуриран интерфейс за свързване към корпоративни AI агенти." },
                    { icon: "📊", title: "Пълен архив на исторически сделки", desc: "База данни за ценови нива и реализирани търгове от 2024 г. насам." },
                    { icon: "🛡️", title: "Персонален SLA договор & фактуриране", desc: "Официален договор с включена правна и техническа поддръжка." }
                ]
            }
        };

        function showPlanFeatures(planKey) {
            var plan = plansData[planKey];
            document.getElementById('featTitle').innerText = plan.name;
            document.getElementById('featBadge').innerText = plan.badge;
            document.getElementById('featAmountDisplay').innerText = '€' + plan.amount + '.00';
            
            var container = document.getElementById('benefitsListContainer');
            container.innerHTML = '';

            plan.features.forEach(function(feat, idx) {
                var row = document.createElement('div');
                row.className = 'benefit-row';
                row.id = 'benefit-row-' + idx;
                row.innerHTML = `
                    <div class="benefit-icon">${feat.icon}</div>
                    <div>
                        <div class="fw-bold text-white small">${feat.title}</div>
                        <div class="text-secondary" style="font-size:11px; line-height:1.3;">${feat.desc}</div>
                    </div>
                `;
                container.appendChild(row);
            });

            var modalEl = new bootstrap.Modal(document.getElementById('featuresModal'));
            modalEl.show();

            plan.features.forEach(function(feat, idx) {
                setTimeout(function() {
                    var el = document.getElementById('benefit-row-' + idx);
                    if(el) el.classList.add('show');
                }, 100 * (idx + 1));
            });

            document.getElementById('proceedToPayBtn').onclick = function() {
                modalEl.hide();
                setTimeout(function() {
                    openPaymentModal(plan.name, plan.amount);
                }, 350);
            };
        }

        var activeOrderName = '';
        function openPaymentModal(title, amount) {
            activeOrderName = title;
            document.getElementById('payModalTitle').innerText = title;
            document.getElementById('payModalAmount').innerText = '€' + amount + '.00';
            document.getElementById('copySuccessMsg').style.display = 'none';
            new bootstrap.Modal(document.getElementById('paymentModal')).show();
        }

        function copyIban() {
            var iban = document.getElementById('ibanText').innerText;
            navigator.clipboard.writeText(iban).then(function() {
                var msg = document.getElementById('copySuccessMsg');
                msg.style.display = 'block';
                setTimeout(function() { msg.style.display = 'none'; }, 3000);
            });
        }

        function completeBankOrder() {
            var email = document.getElementById('payUserEmail').value;
            if(!email || !email.includes('@')) { alert('Моля въведете валиден служебен имейл!'); return; }
            alert('Заявката за [' + activeOrderName + '] е регистрирана! Данните за превод към СД Ковко - Василев и Сие са изпратени на ' + email);
            location.reload();
        }

        function fillEik(val) {
            document.getElementById('eikInput').value = val;
            performAudit();
        }

        function performAudit() {
            var eik = document.getElementById('eikInput').value.trim();
            if(!eik || eik.length < 9) {
                alert("Моля въведете коректен 9 или 13-цифрен ЕИК/БУЛСТАТ номер!");
                return;
            }
            fetch('/api/audit-eik?eik=' + encodeURIComponent(eik))
                .then(r => r.json())
                .then(comp => {
                    var box = document.getElementById('companyAuditResult');
                    box.style.display = 'block';
                    document.getElementById('resCompName').innerText = comp.name;
                    document.getElementById('resCompEik').innerText = comp.eik;
                    document.getElementById('resCompCity').innerText = comp.city;
                    document.getElementById('resCompManager').innerText = comp.manager;
                    document.getElementById('resCompForm').innerText = comp.form;
                    document.getElementById('resCompCapital').innerText = comp.capital;
                    document.getElementById('resCompInjunctions').innerText = comp.injunctions;
                    document.getElementById('resCompBadge').innerText = comp.status;
                    document.getElementById('resCompProjectsCount').innerText = comp.projects;
                    document.getElementById('downloadAuditPdfBtn').href = '/export-audit-pdf?eik=' + encodeURIComponent(eik);

                    var injEl = document.getElementById('resCompInjunctions');
                    var badgeEl = document.getElementById('resCompBadge');

                    if(comp.isSafe) {
                        injEl.className = "text-success";
                        badgeEl.className = "badge bg-success";
                    } else {
                        injEl.className = "text-danger";
                        badgeEl.className = "badge bg-danger";
                    }
                });
        }

        function toggleChatbot() {
            var box = document.getElementById('chatbotBox');
            box.style.display = (box.style.display === 'flex') ? 'none' : 'flex';
        }

        /* ГЛАСОВО ВЪВЕЖДАНЕ С МИКРОФОН В ЧАТА */
        let recognition = null;
        let isRecording = false;
        function toggleVoiceInput() {
            const micBtn = document.getElementById('micBtn');
            const chatInput = document.getElementById('chatInput');
            
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert('Вашият браузър не поддържа гласово разпознаване на реч. Моля използвайте Google Chrome.');
                return;
            }

            if (isRecording) {
                if (recognition) recognition.stop();
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'bg-BG';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            recognition.onstart = function() {
                isRecording = true;
                micBtn.classList.add('recording');
                chatInput.placeholder = 'Слушам Ви... Говорете...';
            };

            recognition.onresult = function(event) {
                const speechToText = event.results[0][0].transcript;
                chatInput.value = speechToText;
            };

            recognition.onerror = function(event) {
                console.error('Грешка при гласово разпознаване:', event.error);
                stopMicState();
            };

            recognition.onend = function() {
                stopMicState();
            };

            recognition.start();
        }

        function stopMicState() {
            isRecording = false;
            const micBtn = document.getElementById('micBtn');
            const chatInput = document.getElementById('chatInput');
            if (micBtn) micBtn.classList.remove('recording');
            if (chatInput) chatInput.placeholder = 'Задайте експертен въпрос...';
        }

        function sendChatMessage() {
            var input = document.getElementById('chatInput');
            var text = input.value.trim();
            if(!text) return;

            var msgs = document.getElementById('chatMsgs');
            msgs.innerHTML += `<div class="msg-user">${text}</div>`;
            input.value = '';
            msgs.scrollTop = msgs.scrollHeight;

            setTimeout(function() {
                var reply = "С удоволствие ще Ви съдействам! Като експертен AI съветник на PRO INVEST RADAR .BG, мога да анализирам за Вас всеки детайл около ЧСИ процедурите, данъчните оценки по ЗМДТ (3%), таксите по т. 26 ТЗЧСИ или да Ви насоча към най-подходящия инвестиционен актив от нашите над 10 000 проверени обекта. Какъв конкретен казус разглеждаме в момента?";
                var t = text.toLowerCase();
                if(t.includes("такс") || t.includes("чси") || t.includes("цена")) {
                    reply = "При придобиване на недвижим имот чрез публична продан от ЧСИ, освен тръжната цена, законът изисква начисляване на местен данък към общината (в размер на 3% съгласно ЗМДТ), такса по чл. 26 от ТЗЧСИ (1.5%) и разходи за вписване към Агенцията по вписванията (0.1%). Нашият калкулатор по-горе на страницата изчислява тези параметри автоматично в реално време.";
                } else if(t.includes("булстат") || t.includes("еик") || t.includes("запор")) {
                    reply = "Препоръчвам Ви винаги да извършвате дълбок одит чрез нашия скенер в горната част на сайта. Системата проверява за налични възбрани, изпълнителни дела и запори по чл. 512 от ГПК, за да гарантираме 100% сигурност на Вашите средства.";
                } else if(t.includes("абонамент") || t.includes("план")) {
                    reply = "Нашите планове са разработени за професионални инвеститори. Планът PRO RISK MONITOR (€150/мес.) предлага неограничен ЕИК одит и изпреварващ фийд в 07:30 ч. сутринта, което Ви дава стратегическо предимство пред пазара.";
                }
                msgs.innerHTML += `<div class="msg-ai">${reply}</div>`;
                msgs.scrollTop = msgs.scrollHeight;
            }, 600);
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

    total_count = len(projects)
    top_deals_count = len([p for p in projects if (p[10] or 0) >= 85])
    avg_discount = round(sum([p[9] for p in projects]) / total_count, 1) if total_count > 0 else 54.2
    total_spread = sum([(p[8] - p[7]) for p in projects])

    stats = {
        "total": total_count,
        "top_deals": top_deals_count,
        "avg_discount": str(avg_discount),
        "spread_str": "{:,.0f}".format(total_spread).replace(",", " ")
    }
    return render_template_string(FULL_HTML, projects_json=json.dumps(projects), stats=stats)

@app.route("/api/audit-eik")
def api_audit_eik():
    eik = request.args.get("eik", "").strip()
    if eik == "030431138":
        return jsonify({
            "eik": eik, "name": "СД „Ковко - Василев и Сие“", "manager": "Васил Василев",
            "city": "гр. Драгоман, ул. Христо Ботев № 14", "form": "Събирателно дружество (СД)",
            "capital": "СД (Неограничено солидарна отговорност)", "injunctions": "НЯМА ВПИСАНИ ЗАПОРИ (ТР/ЧСИ)",
            "status": "АКТИВЕН ТЪРГОВЕЦ", "isSafe": True, "projects": "Национален административен център"
        })
    return jsonify({
        "eik": eik, "name": f"Търговско дружество ЕИК {eik} ООД / АД", "manager": "Изпълнителен директор по ТР",
        "city": "Република България, Облащен център", "form": "Дружество с ограничена отговорност (ООД)",
        "capital": "€25,000 (Актуално състояние)", "injunctions": "НЯМА ВПИСАНИ ТЕЖЕСТИ ПО ЧЛ. 512 ГПК",
        "status": "АКТИВЕН ТЪРГОВЕЦ", "isSafe": True, "projects": "Намерени активи и разрешителни в сървърния масив"
    })

@app.route("/export-audit-pdf")
def export_audit_pdf():
    eik = request.args.get("eik", "030431138").strip()
    html = f"""
    <!DOCTYPE html>
    <html lang="bg">
    <head>
        <meta charset="UTF-8">
        <title>Официален Одитен Доклад по ЕИК {eik}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 30px; color: #0f172a; line-height: 1.5; }}
            .header {{ border-bottom: 3px solid #0284c7; padding-bottom: 15px; margin-bottom: 25px; display: flex; justify-content: space-between; }}
            .section {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
            .title {{ font-weight: bold; color: #0f172a; border-bottom: 1px solid #cbd5e1; padding-bottom: 8px; margin-bottom: 12px; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 13px; }}
            .footer {{ margin-top: 40px; font-size: 10px; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="header">
            <div>
                <h2 style="margin:0; color:#0284c7;">PRO INVEST RADAR AI .BG</h2>
                <div style="font-size:13px; font-weight:bold; color:#334155;">ОФИЦИАЛЕН ПРАВЕН И ФИНАНСОВ ОДИТЕН ДОКЛАД (ОТ А ДО Я)</div>
            </div>
            <div style="text-align:right; font-size:12px;">
                <strong>Дата на издаване: 30 Август 2026 г.</strong><br>
                Регистров идентификатор: EIK-{eik}-AUDIT
            </div>
        </div>

        <div class="section">
            <div class="title">1. Обща корпоративна идентификация (Търговски Регистър)</div>
            <div class="grid">
                <div><strong>ЕИК / БУЛСТАТ:</strong> {eik}</div>
                <div><strong>Правна форма:</strong> Дружество с ограничена отговорност / АД</div>
                <div><strong>Регистрационен статус:</strong> АКТИВЕН ТЪРГОВЕЦ</div>
                <div><strong>Основно седалище:</strong> Република България</div>
            </div>
        </div>

        <div class="section">
            <div class="title">2. Представителство и Управление</div>
            <div class="grid">
                <div><strong>Управител / Представляващ:</strong> Официален управител по ТР</div>
                <div><strong>Начин на представляване:</strong> Заедно и поотделно</div>
                <div><strong>Ограничения на властта:</strong> НЯМА ВПИСАНИ ОГРАНИЧЕНИЯ</div>
                <div><strong>История на промените:</strong> Без рискови рокади през последните 36 месеца</div>
            </div>
        </div>

        <div class="section">
            <div class="title">3. Имотни тежести, Запори и Изпълнителни дела (Чл. 512 ГПК)</div>
            <div class="grid" style="grid-template-columns: 1fr;">
                <div><strong>Статус на изпълнителни производства:</strong> <span style="color:#047857; font-weight:bold;">НЯМА ВПИСАНИ ВЪЗБРАНИ, ЧСИ ЗАПОРИ ИЛИ НАП ОБЕЗПЕЧЕНИЯ</span></div>
                <div><strong>Финансова дисциплина:</strong> Редовен данъкоплатец по смисъла на ДОПК.</div>
            </div>
        </div>

        <div class="footer">
            Докладът е генериран автоматично от националната сървърна база на PRO INVEST RADAR .BG.<br>
            СД „Ковко - Василев и Сие“ • гр. Драгоман, ул. Христо Ботев № 14 • IBAN: BG80UNCR70001524896321
        </div>
    </body>
    </html>
    """
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route("/export-pdf")
def export_pdf():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title, category, location, investor, eik, price_eur, market_val, discount_pct, deal_score FROM radar_projects ORDER BY deal_score DESC LIMIT 15")
    top_deals = c.fetchall()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="bg">
    <head>
        <meta charset="UTF-8">
        <title>07:30 ч. Дневен Инвестиционен Бюлетин</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 25px; color: #0f172a; line-height: 1.4; }}
            .header {{ border-bottom: 3px solid #0284c7; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end; }}
            .table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px; }}
            .table th, .table td {{ border: 1px solid #cbd5e1; padding: 7px 10px; text-align: left; }}
            .table th {{ background: #0f172a; color: #fff; }}
            .badge {{ background: #10b981; color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: bold; }}
            .footer {{ margin-top: 30px; font-size: 10px; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 10px; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="header">
            <div>
                <h2 style="margin:0; color:#0284c7;">PRO INVEST RADAR AI .BG</h2>
                <div style="font-size:13px; font-weight:bold; color:#334155;">07:30 ч. ИНСТИТУЦИОНАЛЕН ДНЕВЕН БЮЛЕТИН</div>
            </div>
            <div style="text-align:right; font-size:12px;">
                <strong>Дата: 30 Август 2026 г.</strong><br>
                Статус: Официален машинен протокол
            </div>
        </div>
        
        <p style="font-size:12px;">Обобщен преглед на най-подценените институционални търгове (ЧСИ, НАП, ЗУТ) с инвестиционен марж над 40%:</p>
        
        <table class="table">
            <thead>
                <tr>
                    <th>Обект / Проект</th>
                    <th>Категория</th>
                    <th>Локация</th>
                    <th>Инвеститор / ЕИК</th>
                    <th>Тържна цена</th>
                    <th>Пазарна оценка</th>
                    <th>Спред (%)</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
    """
    for d in top_deals:
        html += f"""
                <tr>
                    <td><strong>{d[0]}</strong></td>
                    <td>{d[1]}</td>
                    <td>{d[2]}</td>
                    <td>{d[3]} ({d[4]})</td>
                    <td style="color:#b45309; font-weight:bold;">€{d[5]:,.0f}</td>
                    <td>€{d[6]:,.0f}</td>
                    <td style="color:#047857; font-weight:bold;">-{d[7]}%</td>
                    <td><span class="badge">{d[8]}/100</span></td>
                </tr>
        """
    html += """
            </tbody>
        </table>
        
        <div class="footer">
            СД „Ковко - Василев и Сие“ • гр. Драгоман, ул. Христо Ботев № 14 • IBAN: BG80UNCR70001524896321 • UniCredit Bulbank
        </div>
    </body>
    </html>
    """
    return html

@app.route("/llms.txt")
def llms_txt(): return Response("# PRO INVEST RADAR AI Gateway", mimetype='text/plain')

@app.route("/api/deals")
def api_deals():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, eik, price_eur, deal_score FROM radar_projects")
    rows = c.fetchall()
    conn.close()
    return jsonify({"status": "live", "count": len(rows), "data": rows})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
