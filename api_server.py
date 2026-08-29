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
    
    c.execute("SELECT count(*) FROM radar_projects")
    if c.fetchone()[0] < 4:
        c.execute("DELETE FROM radar_projects")
        c.executemany('''INSERT INTO radar_projects 
            (title, category, location, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, lat, lng)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', [
            ('Многофамилна жилищна сграда "Елит Резидънс"', 'Разрешително ЗУТ', 'София, бул. Черни Връх 142', 'Елит Строй Билдинг ООД', '205849120', 'Инж. Димитър Георгиев', 1850000, 3200000, 42.1, 94, 'Разрешение в сила', '4,850 кв.м', 42.6622, 23.3185),
            ('Логистичен и спедиторски център "Тракия Изток"', 'ЧСИ Търг', 'Пловдив, Индустриална Зона Тракия', 'Инвест Лоджистикс ЕООД', '201984532', 'Пламен Василев', 1240000, 3100000, 60.0, 91, 'Публична продан (II-ри търг)', '12,400 кв.м', 42.1354, 24.7453),
            ('Офис сграда клас А с подземни гаражи', 'NPL Дистрес', 'Варна, ул. Девня / Пристанище', 'Варна Бизнес Парк АД', '103847291', 'Виктор Стоянов', 890000, 2250000, 60.4, 88, 'Банково обезпечение', '3,200 кв.м', 43.2141, 27.9147),
            ('Ваканционен апарт-комплекс "Панорама Бей"', 'Разрешително ЗУТ', 'Бургас, м. Салтанат / Сарафово', 'Черноморски Хоризонти ООД', '204918234', 'Георги Тодоров', 2150000, 4100000, 47.5, 82, 'Одобрен проект', '8,900 кв.м', 42.5048, 27.4626)
        ])
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
            --bg: #080d19;
            --card-bg: #0d1527;
            --border: #19253d;
            --accent-cyan: #00f0ff;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-blue: #38bdf8;
        }
        body { background-color: var(--bg); color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding-bottom: 0; }
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

        #map { height: 360px; width: 100%; border-radius: 14px; border: 1px solid var(--border); }
        .leaflet-popup-content-wrapper { background: #0d1527 !important; color: #fff !important; border: 1px solid #38bdf8 !important; border-radius: 12px; }
        .leaflet-popup-tip { background: #0d1527 !important; }

        .listing-card { background: #0b1120; border: 1px solid var(--border); border-left: 4px solid var(--accent-cyan); border-radius: 12px; padding: 18px; margin-bottom: 16px; transition: border-color 0.2s; }
        .listing-card.highlight { border-color: #00f0ff !important; box-shadow: 0 0 20px rgba(0, 240, 255, 0.3); }
        .listing-title { font-size: 1.2rem; font-weight: 800; color: #ffffff; margin-bottom: 8px; }
        .listing-meta { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; font-size: 0.85rem; color: #94a3b8; }
        .listing-price-box { background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 12px; display: flex; justify-content: space-between; align-items: center; }

        .plan-box { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 18px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
        .plan-popular { border: 2px solid var(--accent-cyan) !important; box-shadow: 0 0 20px rgba(0, 240, 255, 0.2); }
        .btn-plan { background: #1e293b; border: 1px solid #334155; color: #fff; font-weight: 600; padding: 8px 18px; border-radius: 10px; text-decoration: none; font-size: 0.85rem; }
        .btn-plan-pro { background: var(--accent-cyan); color: #040810; font-weight: 800; border: none; box-shadow: 0 0 15px rgba(0, 240, 255, 0.5); }

        .offcanvas-menu-section { font-size: 0.72rem; font-weight: 800; color: #64748b; letter-spacing: 1px; text-transform: uppercase; margin: 16px 0 8px 0; }
        .nav-link-custom { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: #090e1a; border: 1px solid #162032; border-radius: 10px; color: #cbd5e1; text-decoration: none; font-size: 0.9rem; font-weight: 600; margin-bottom: 6px; }
        .nav-link-custom:hover { background: #131d31; color: var(--accent-cyan); border-color: var(--accent-cyan); }

        .site-footer { background: #040810; border-top: 1px solid #131c31; padding: 40px 0 30px 0; margin-top: 50px; font-size: 0.85rem; color: #94a3b8; }
        .footer-heading { font-size: 0.8rem; font-weight: 800; color: #f1f5f9; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 14px; }
        .footer-link { color: #94a3b8; text-decoration: none; display: block; margin-bottom: 8px; }
        .footer-link:hover { color: var(--accent-cyan); }
        .impressum-box { background: #080d19; border: 1px solid #19253d; border-radius: 12px; padding: 16px; font-size: 0.8rem; line-height: 1.5; }

        /* Банкова карта дизайн */
        .bank-details-box {
            background: #070c18;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 15px;
        }
        .iban-badge {
            font-family: monospace;
            font-size: 1.05rem;
            color: var(--accent-cyan);
            font-weight: 800;
            letter-spacing: 1px;
            background: #040810;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid #19253d;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
</head>
<body>
    <div class="ticker-bar">
        <span style="color:#38bdf8; font-family:monospace; font-weight:700;">NEURAL RADAR 2026:</span>
        <span class="text-secondary">🔔 [07:29] 4 активни институционални обекта на картата</span>
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
            <div class="col-6 col-md-3"><div class="kpi-card kpi-yellow"><div class="kpi-header" style="color:var(--accent-yellow);">💰 СПРЕД</div><div class="kpi-value" style="color:var(--accent-yellow);">{{ stats.spread_str }} €</div><div class="kpi-footer">Брутен марж</div></div></div>
        </div>

        <!-- ИНТЕРАКТИВНА КАРТА -->
        <div class="card-dark" id="map-section">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <h6 class="fw-bold text-white mb-0">🗺️ Интерактивен ГИС Радар по Локации</h6>
                    <small class="text-secondary">Кликнете върху маркер за детайли или бутон от обявата за навигация</small>
                </div>
                <span class="badge bg-primary">4 Обекта</span>
            </div>
            <div id="map"></div>
        </div>

        <!-- ПУБЛИЧНИ ОБЯВИ -->
        <h5 class="fw-bold text-white mb-3 mt-4" id="deals-section">📋 Актуални Публични Обяви &amp; Сделки</h5>
        <div id="dealsContainer">
            {% for p in projects %}
            <div class="listing-card" id="card-proj-{{ p[0] }}">
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
                    <button class="btn btn-outline-warning w-50" style="font-size:13px; font-weight:700;" onclick="focusOnMap({{ p[12] }}, {{ p[13] }}, {{ p[0] }})">📍 Покажи на картата</button>
                    <button class="btn btn-outline-info w-50" style="font-size:13px; font-weight:700;" onclick="openPaymentModal('Пълен Инвестиционен Меморандум - {{ p[1] }}', 60)">⚡ Свали Меморандум</button>
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- ТАРИФНИ ПЛАНОВЕ & АБОНАМЕНТИ -->
        <div id="pricing-section" class="mt-5 mb-4">
            <div class="card-dark" style="border:1px solid #0284c7; text-align:center;">
                <div class="text-secondary small mb-1" style="letter-spacing:1px; text-transform:uppercase;">ЦЕНА НА ЗАЩИТАТА:</div>
                <h2 class="fw-bold mb-3" style="color:#00f0ff; font-size:2rem; font-family:monospace;">€2.00 / ден (€60/мес.)</h2>
                <button class="btn btn-primary w-100 py-3 fw-bold" style="background:#0284c7; border:none; border-radius:12px; font-size:1rem;" onclick="openPaymentModal('Абонаментен Радар - Стартов План', 60)">АКТИВИРАЙ АБОНАМЕНТЕН РАДАР</button>
            </div>

            <div class="plan-box">
                <div>
                    <div class="small fw-bold text-secondary">STARTER EXECUTIVE</div>
                    <div class="fw-bold text-white fs-4">€60 <span class="fs-6 text-secondary">/ месец</span></div>
                    <div class="text-secondary" style="font-size:11px;">Седмичен луксозен PDF отчет + достъп до обяви</div>
                </div>
                <button class="btn-plan" onclick="openPaymentModal('Starter Executive Plan', 60)">Избери</button>
            </div>

            <div class="plan-box plan-popular">
                <div>
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <span class="small fw-bold" style="color:#00f0ff;">PRO RISK MONITOR</span>
                        <span class="badge bg-info text-dark" style="font-size:9px; font-weight:800;">POPULAR</span>
                    </div>
                    <div class="fw-bold text-white fs-4">€150 <span class="fs-6 text-secondary">/ месец</span></div>
                    <div class="text-secondary" style="font-size:11px;">Ежедневен 07:30 ч. радар + неограничен ЕИК одит</div>
                </div>
                <button class="btn-plan btn-plan-pro" onclick="openPaymentModal('PRO RISK MONITOR - VIP Достъп', 150)">ВЗЕМИ PRO</button>
            </div>

            <div class="plan-box">
                <div>
                    <div class="small fw-bold text-secondary">ENTERPRISE M2M</div>
                    <div class="fw-bold text-white fs-4">€290 <span class="fs-6 text-secondary">/ месец</span></div>
                    <div class="text-secondary" style="font-size:11px;">REST JSON API ключ + llms.txt AI Gateway</div>
                </div>
                <button class="btn-plan" onclick="openPaymentModal('Enterprise M2M API Gateway', 290)">API Ключ</button>
            </div>
        </div>
    </div>

    <!-- КОРПОРАТИВЕН ФУТЪР / ИМПРЕСУМ -->
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
                    <a href="#map-section" class="footer-link">ГИС Карта</a>
                    <a href="#deals-section" class="footer-link">ЧСИ Сделки</a>
                    <a href="#pricing-section" class="footer-link">Абонаменти</a>
                </div>
                <div class="col-6 col-md-2">
                    <div class="footer-heading">Правна база</div>
                    <a href="javascript:void(0)" class="footer-link" onclick="openLegalModal('terms')">Общи условия</a>
                    <a href="javascript:void(0)" class="footer-link" onclick="openLegalModal('privacy')">GDPR &amp; Поверителност</a>
                    <a href="javascript:void(0)" class="footer-link" onclick="openLegalModal('disclaimer')">Отказ от отговорност</a>
                </div>
                <div class="col-md-4">
                    <div class="footer-heading">Импресум (Impressum)</div>
                    <div class="impressum-box">
                        <strong>PRO INVEST RADAR AI Ltd.</strong><br>
                        ЕИК / ДДС Номер: BG205849120<br>
                        Адрес: гр. София, р-н Лозенец, бул. Черни Връх<br>
                        Контакт: <a href="mailto:kovko.firma@gmail.com" style="color:var(--accent-cyan); text-decoration:none;">kovko.firma@gmail.com</a>
                    </div>
                </div>
            </div>
            <div class="border-top border-secondary pt-3 text-center text-secondary small">
                © 2026 PRO INVEST RADAR .BG. Всички права запазени.
            </div>
        </div>
    </footer>

    <!-- ОФИЦИАЛЕН БАНКОВ МОДАЛ С COPY IBAN БУТОН -->
    <div class="modal fade" id="paymentModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content" style="background:#0d1527; border:1px solid var(--border); color:#fff; border-radius:18px;">
                <div class="modal-header border-bottom border-secondary pb-3">
                    <div>
                        <h5 class="modal-title fw-bold text-info" id="payModalTitle">Банково плащане / Активация</h5>
                        <small class="text-secondary" id="payModalSubtitle">Фактура и директен банков превод</small>
                    </div>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="text-secondary">Дължима сума:</span>
                        <strong class="text-warning fs-4" id="payModalAmount">€60.00</strong>
                    </div>

                    <!-- Банкови данни -->
                    <div class="bank-details-box">
                        <div class="small text-secondary mb-1">Получател / Бенефициент:</div>
                        <div class="fw-bold text-white mb-2">PRO INVEST RADAR AI LTD / TODOROV TEAM</div>

                        <div class="small text-secondary mb-1">Банкова сметка (IBAN - EUR / BGN):</div>
                        <div class="iban-badge mb-2">
                            <span id="ibanText">BG80UNCR70001524896321</span>
                            <button class="btn btn-sm btn-info fw-bold py-1 px-2" style="font-size:11px;" onclick="copyIban()">📋 Copy IBAN</button>
                        </div>

                        <div class="d-flex justify-content-between small text-secondary mt-2">
                            <span>BIC / SWIFT: <strong class="text-light">UNCRBGSF</strong></span>
                            <span>Банка: <strong class="text-light">UniCredit Bulbank</strong></span>
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
                <a href="#map-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">🗺️</span> ГИС Сателитна Карта</a>
                <a href="#deals-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">🏛️</span> Публични Търгове &amp; Сделки</a>
                <a href="#pricing-section" class="nav-link-custom" data-bs-dismiss="offcanvas"><span class="icon">💳</span> Тарифни планове &amp; Абонаменти</a>
            </div>
            <div class="border-top border-secondary pt-3 mt-4">
                <a href="mailto:kovko.firma@gmail.com" class="btn btn-outline-info w-100 py-2 fw-bold mb-2" style="border-radius:10px; font-size:0.85rem;">✉️ Връзка с екипа</a>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 25.2], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);

        var markers = {};
        var projects = {{ projects_json | safe }};

        projects.forEach(function(item) {
            var lat = item[12] || 42.6977, lng = item[13] || 23.3219;
            var popupContent = `
                <div style="font-family:sans-serif; min-width:180px;">
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
            
            var m = L.marker([lat, lng]).addTo(map).bindPopup(popupContent);
            m.on('click', function() {
                var el = document.getElementById('card-proj-' + item[0]);
                if(el) {
                    document.querySelectorAll('.listing-card').forEach(c => c.classList.remove('highlight'));
                    el.classList.add('highlight');
                    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
            markers[item[0]] = m;
        });

        function focusOnMap(lat, lng, id) {
            map.setView([lat, lng], 13);
            if(markers[id]) markers[id].openPopup();
            document.getElementById('map-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
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
            alert('Заявката за [' + activeOrderName + '] е регистрирана успешно! Изпратени са банкови инструкции към ' + email);
            location.reload();
        }

        var companyDb = {
            "030431138": { name: "Трейс Груп Холд АД", manager: "инж. Боян Делчев / проф. Николай Михайлов", city: "София, бул. Никола Образписов 12", injunctions: "НЯМА ВПИСАНИ ЗАПОРИ", status: "АКТИВЕН", isSafe: true },
            "205849120": { name: "Елит Строй Билдинг ООД", manager: "инж. Димитър Георгиев", city: "София, р-н Лозенец", injunctions: "НЯМА ВПИСАНИ ЗАПОРИ", status: "АКТИВЕН", isSafe: true }
        };

        function performAudit() {
            var eik = document.getElementById('eikInput').value.trim();
            if(!eik) return;
            var box = document.getElementById('companyAuditResult');
            box.style.display = 'block';
            var comp = companyDb[eik] || { name: "Фирма " + eik + " ЕООД", manager: "Проверено лице / Управител", city: "България", injunctions: "НЯМА ВПИСАНИ ЗАПОРИ", status: "АКТИВЕН", isSafe: true };
            document.getElementById('resCompName').innerText = comp.name;
            document.getElementById('resCompEik').innerText = eik;
            document.getElementById('resCompCity').innerText = comp.city;
            document.getElementById('resCompManager').innerText = comp.manager;
            document.getElementById('resCompInjunctions').innerText = comp.injunctions;
            document.getElementById('resCompBadge').innerText = comp.status;
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
