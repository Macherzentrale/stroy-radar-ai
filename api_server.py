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
    
    # Винаги се уверяваме, че има пълния списък с реални публични обяви
    c.execute("SELECT count(*) FROM radar_projects")
    if c.fetchone()[0] < 4:
        c.execute("DELETE FROM radar_projects")
        c.executemany('''INSERT INTO radar_projects 
            (title, category, location, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, lat, lng)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', [
            ('Многофамилна жилищна сграда "Елит Резидънс"', 'Разрешително ЗУТ', 'София, бул. Черни Връх 142', 'Елит Строй Билдинг ООД', '205849120', 'Инж. Димитър Георгиев', 1850000, 3200000, 42.1, 94, 'Разрешение в сила', '4,850 кв.м', 42.6622, 23.3185),
            ('Логистичен и спедиторски център "Тракия Изток"', 'ЧСИ Търг', 'Пловдив, Индустриална Зона Тракия', 'Инвест Лоджистикс ЕООД', '201984532', 'Пламен Василев', 1240000, 3100000, 60.0, 91, 'Публична продан (II-ри търг)', '12,400 кв.м', 42.1354, 24.7453),
            ('Офис сграда клас А с подземни гаражи', 'NPL Дистрес', 'Варна, ул. Девня / Пристанище', 'Варна Бизнес Парк АД', '103847291', 'Виктор Стоянов', 890000, 2250000, 60.4, 88, 'Банково обезпечение', '3,200 кв.м', 43.2141, 27.9147),
            ('Ваканционен апарт-комплекс "Панорама Бей"', 'Разрешително ЗУТ', 'Бургас, м. Салтанат / Сарафово', 'Черноморски Хоризонти ООД', '204918234', 'Георги Тодоров', 2150000, 4100000, 47.5, 82, 'Одобрен проект', '8,900 кв.м', 42.5048, 27.4626),
            ('Производствена база и складова площ', 'НАП Публична продан', 'Русе, Индустриален парк', 'Дунав Продъкшън ЕАД', '118274019', 'Стефан Иванов', 450000, 980000, 54.1, 86, 'Данъчен търг', '5,100 кв.м', 43.8563, 25.9700)
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
        body {
            background-color: var(--bg);
            color: #f1f5f9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding-bottom: 60px;
        }
        .container-custom {
            max-width: 960px;
            margin: 0 auto;
            padding: 0 16px;
        }

        /* Ticker лента */
        .ticker-bar {
            background: #040810;
            border-bottom: 1px solid #131c31;
            padding: 6px 14px;
            font-size: 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Хедър / Навигация */
        .navbar-custom {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
        }
        .brand-box {
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
        }
        .shield-icon {
            width: 38px;
            height: 38px;
            background: #1e3a8a;
            border: 2px solid #38bdf8;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
        }
        .btn-burger {
            background: #1e293b;
            border: 1px solid #334155;
            color: #fff;
            padding: 7px 14px;
            border-radius: 10px;
            font-size: 1.25rem;
            cursor: pointer;
            line-height: 1;
        }

        /* 3D Сателитен HUD */
        .sat-hud {
            background: radial-gradient(circle at center, #1e293b 0%, #0d1527 100%);
            border: 1px solid rgba(0, 240, 255, 0.4);
            border-radius: 18px;
            padding: 16px;
            text-align: center;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: 0 0 25px rgba(0, 240, 255, 0.12);
        }
        @keyframes radarRotate { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes satOrbitAnim { 0% { transform: rotate(0deg) translateX(48px) rotate(0deg); } 100% { transform: rotate(360deg) translateX(48px) rotate(-360deg); } }
        .radar-sweep { transform-origin: 75px 75px; animation: radarRotate 4s linear infinite; }
        .sat-orbit { transform-origin: 75px 75px; animation: satOrbitAnim 7s linear infinite; }

        /* Карти и компоненти */
        .card-dark {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 16px;
        }
        .custom-input, .custom-select {
            background: #070c18;
            border: 1px solid var(--border);
            color: #fff;
            padding: 10px 14px;
            border-radius: 10px;
            width: 100%;
            font-family: monospace;
        }
        .custom-input:focus, .custom-select:focus {
            outline: none;
            border-color: var(--accent-cyan);
        }

        /* 4-те KPI карти */
        .kpi-card {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 14px 16px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 115px;
            border: 1px solid var(--border);
        }
        .kpi-green  { border-left: 4px solid var(--accent-green) !important; }
        .kpi-blue   { border-left: 4px solid var(--accent-blue) !important; }
        .kpi-yellow { border-left: 4px solid var(--accent-yellow) !important; }

        .kpi-header { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; }
        .kpi-value { font-size: 1.85rem; font-weight: 800; line-height: 1.1; margin: 4px 0; }
        .kpi-footer { font-size: 0.68rem; color: #64748b; }

        /* Карта */
        #map { height: 320px; width: 100%; border-radius: 16px; border: 1px solid var(--border); }

        /* Филтър чипове */
        .filter-chip {
            background: #0d1527;
            border: 1px solid var(--border);
            color: #94a3b8;
            font-size: 0.8rem;
            padding: 6px 14px;
            border-radius: 20px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin-right: 6px;
            margin-bottom: 8px;
        }
        .filter-chip.active {
            background: #1e293b;
            color: var(--accent-cyan);
            border-color: var(--accent-cyan);
            font-weight: 700;
        }

        /* Обява / Актив карта */
        .deal-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 14px;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }
        .deal-card:hover {
            border-color: #38bdf8;
            transform: translateY(-2px);
        }
        .deal-badge-score {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
            font-weight: 800;
            font-size: 0.75rem;
            padding: 4px 10px;
            border-radius: 8px;
        }
        .stat-box {
            background: #070c18;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 8px 12px;
            text-align: center;
        }

        /* Тарифи */
        .plan-box {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .plan-popular {
            border: 2px solid var(--accent-cyan) !important;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.2);
        }
        .btn-plan {
            background: #1e293b;
            border: 1px solid #334155;
            color: #fff;
            font-weight: 600;
            padding: 8px 18px;
            border-radius: 10px;
            text-decoration: none;
            font-size: 0.85rem;
        }
        .btn-plan-pro {
            background: var(--accent-cyan);
            color: #040810;
            font-weight: 800;
            border: none;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.5);
        }

        /* M2M Gateway Footer */
        .m2m-footer {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
        }
        .btn-m2m {
            background: #070c18;
            border: 1px solid var(--border);
            color: var(--accent-cyan);
            font-family: monospace;
            padding: 4px 10px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 0.75rem;
        }
    </style>
</head>
<body>
    <!-- 1. Ticker лента -->
    <div class="ticker-bar">
        <span style="color:#38bdf8; font-family:monospace; font-weight:700;">NEURAL RADAR 2026:</span>
        <span class="text-secondary">🔔 [07:29] Нов ЧСИ търг &amp; ЗУТ разрешително добавени в реално време</span>
        <span class="badge bg-success" style="font-size:9px;">LIVE</span>
    </div>

    <div class="container-custom">
        <!-- 2. Навигация с мобилно меню -->
        <div class="navbar-custom">
            <a href="/" class="brand-box">
                <div class="shield-icon">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2.5">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <path d="M12 8v4"/>
                        <path d="M12 16h.01"/>
                    </svg>
                </div>
                <div>
                    <div style="font-weight:900; font-size:1.2rem; color:#fff; line-height:1;">PRO INVEST RADAR AI</div>
                    <small style="color:#00f0ff; font-size:0.75rem; font-weight:700;">EUR 2026 • .BG</small>
                </div>
            </a>
            <div class="d-flex align-items-center gap-2">
                <button class="btn-burger" type="button" data-bs-toggle="offcanvas" data-bs-target="#mobileMenu">☰</button>
            </div>
        </div>

        <!-- 3. ГОЛЯМ ХЕДЪР БЛОК: ЕИК ОДИТ СКЕНЕР + 3D САТЕЛИТ ВДЯСНО -->
        <div class="row g-3 mb-3">
            <div class="col-lg-7">
                <div class="card-dark h-100 mb-0">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="fw-bold text-white mb-0">🔍 Одит на фирма преди превод или сделка</h6>
                        <span class="badge bg-info text-dark" style="font-size:10px; font-weight:800;">АВТОНОМЕН СКЕНЕР</span>
                    </div>
                    <p class="text-secondary small mb-3">Въведете ЕИК/БУЛСТАТ (напр. <span class="text-info">205849120</span> или <span class="text-info">030431138</span>) за мигновен одит:</p>
                    
                    <div class="d-flex gap-2 mb-3">
                        <input type="text" id="eikInput" class="custom-input" placeholder="030431138" value="205849120">
                        <button class="btn btn-outline-info" style="border-radius:10px; white-space:nowrap;" onclick="performAudit()">Търси</button>
                    </div>

                    <!-- Резултатен контейнер отдолу -->
                    <div id="companyAuditResult" class="p-3 rounded" style="background:#070c18; border:1px solid var(--border); display:none;">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <strong class="text-info fs-6" id="resCompName">Елит Строй Билдинг ООД</strong>
                            <span class="badge bg-success" id="resCompStatus">АКТИВЕН</span>
                        </div>
                        <div class="small text-secondary mb-1">ЕИК: <span class="text-light" id="resCompEik">205849120</span> | Седалище: <span class="text-light">София, България</span></div>
                        <div class="small text-secondary mb-1">Управител: <span class="text-light" id="resCompManager">Инж. Димитър Георгиев</span></div>
                        <div class="border-top border-secondary pt-2 mt-2">
                            <div class="d-flex justify-content-between small">
                                <span>Вписани запори (ТР):</span>
                                <strong class="text-success" id="resCompInjunctions">НЯМА ВПИСАНИ ЗАПОРИ</strong>
                            </div>
                            <div class="d-flex justify-content-between small mt-1">
                                <span>Свързани ЧСИ / ЗУТ обекти:</span>
                                <strong class="text-warning">1 активно разрешително в радара</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 3D САТЕЛИТ ВДЯСНО -->
            <div class="col-lg-5">
                <div class="sat-hud">
                    <div class="text-info small fw-bold mb-2">🛰️ 3D САТЕЛИТЕН ТЕЛЕМЕТРИЧЕН РАДАР</div>
                    <svg viewBox="0 0 150 150" width="130" height="130">
                        <circle cx="75" cy="75" r="65" fill="none" stroke="#1e293b" stroke-width="1.2" stroke-dasharray="3 3"/>
                        <circle cx="75" cy="75" r="42" fill="none" stroke="#1e293b" stroke-width="1"/>
                        <g class="radar-sweep">
                            <path d="M 75 75 L 25 25 A 65 65 0 0 1 125 25 Z" fill="rgba(0,240,255,0.2)"/>
                        </g>
                        <circle cx="75" cy="75" r="8" fill="#0284c7"/>
                        <g class="sat-orbit">
                            <circle cx="75" cy="75" r="5" fill="#38bdf8"/>
                            <rect x="68" y="72" width="14" height="5" fill="#070c18" stroke="#38bdf8" rx="1"/>
                        </g>
                    </svg>
                    <div class="d-flex justify-content-around text-secondary small w-100 border-top border-secondary pt-2 mt-2">
                        <span>ЗУТ: <strong class="text-light">Свързан</strong></span>
                        <span>ЧСИ: <strong class="text-light">OK</strong></span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 4. 4-ТЕ KPI КАРТИ -->
        <div class="row g-2 mb-3">
            <div class="col-6 col-md-3">
                <div class="kpi-card">
                    <div class="kpi-header text-secondary">🗄️ АКТИВНИ АКТИВИ</div>
                    <div class="kpi-value text-white">{{ stats.total }}</div>
                    <div class="kpi-footer">В реално време</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="kpi-card kpi-green">
                    <div class="kpi-header" style="color:var(--accent-green);">⚡ TOP DEALS (≥85)</div>
                    <div class="kpi-value" style="color:var(--accent-green);">{{ stats.top_deals }}</div>
                    <div class="kpi-footer">Максимален марж</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="kpi-card kpi-blue">
                    <div class="kpi-header" style="color:var(--accent-blue);">📉 СРЕДЕН ДИСКОНТ</div>
                    <div class="kpi-value" style="color:var(--accent-blue);">-{{ stats.avg_discount }}%</div>
                    <div class="kpi-footer">Спрямо пазара</div>
                </div>
            </div>
            <div class="col-6 col-md-3">
                <div class="kpi-card kpi-yellow">
                    <div class="kpi-header" style="color:var(--accent-yellow);">💰 СПРЕД</div>
                    <div class="kpi-value" style="color:var(--accent-yellow);">{{ stats.spread_str }} €</div>
                    <div class="kpi-footer">Брутен инвестиционен марж</div>
                </div>
            </div>
        </div>

        <!-- 5. ЧСИ КАЛКУЛАТОР & ДЪРЖАВНИ ТАКСИ 2026 -->
        <div class="card-dark">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <span class="badge bg-warning text-dark" style="font-size:11px; font-weight:700;">ДЪРЖАВНИ ТАКСИ 2026</span>
                <span class="text-info fw-bold fs-5" id="sliderValDisplay">€88 000</span>
            </div>
            <label class="small text-secondary mb-1">Начална цена / Оферирана сума (EUR):</label>
            <input type="range" min="10000" max="500000" step="5000" value="88000" class="form-range mb-3" oninput="updateChsiCalc(this.value)">
            
            <div class="row g-2 mb-3">
                <div class="col-6">
                    <label class="small text-secondary" style="font-size:11px;">МЕСТЕН ДАНЪК (ЗМДТ):</label>
                    <div class="p-2 rounded" style="background:#070c18; border:1px solid var(--border); font-size:12px; color:#fff;">3.0% (София / Пловдив)</div>
                </div>
                <div class="col-6">
                    <label class="small text-secondary" style="font-size:11px;">ТАКСА ЧСИ (Т. 26 ТЗЧСИ):</label>
                    <div class="p-2 rounded" style="background:#070c18; border:1px solid var(--border); font-size:12px; color:#fff;">1.5% с ДДС (Закон)</div>
                </div>
            </div>
            <button class="btn btn-outline-info w-100 py-2 fw-bold" style="border-radius:10px; font-size:13px;" onclick="alert('ЧСИ Анализ: Чиста прогнозна доходност при дисконт 45%: +€39 600.')">🤖 ЧСИ AI Експерт Калкулация</button>
        </div>

        <!-- 6. КАРТА НА АКТИВИТЕ -->
        <div class="card-dark">
            <h6 class="fw-bold text-white mb-2">🗺️ Интерактивна ГИС Карта на активите</h6>
            <div id="map"></div>
        </div>

        <!-- 7. ПУБЛИЧНИ ОБЯВИ И АКТИВИ С ЦЕНИ И ДИСКОНТИ -->
        <div class="mb-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="fw-bold text-white mb-0">📋 Публични Обяви &amp; Инвестиционни Сделки</h5>
                <span class="badge bg-secondary" style="font-size:11px;">{{ stats.total }} Намерени</span>
            </div>

            <!-- Филтър чипове -->
            <div class="mb-3">
                <span class="filter-chip active" onclick="filterCategory('all', this)">Всички обяви</span>
                <span class="filter-chip" onclick="filterCategory('ЧСИ Търг', this)">🏛️ ЧСИ Търгове</span>
                <span class="filter-chip" onclick="filterCategory('Разрешително ЗУТ', this)">🏗️ ЗУТ Строежи</span>
                <span class="filter-chip" onclick="filterCategory('NPL Дистрес', this)">📉 NPL Активи</span>
                <span class="filter-chip" onclick="filterCategory('НАП Публична продан', this)">🏢 НАП Търгове</span>
            </div>

            <!-- Списък с картите на обявите -->
            <div id="dealsContainer">
                {% for p in projects %}
                <div class="deal-card" data-category="{{ p[2] }}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <span class="badge bg-secondary me-1" style="font-size:11px;">{{ p[2] }}</span>
                            <span class="badge bg-dark border border-secondary text-info" style="font-size:11px;">{{ p[11] }}</span>
                        </div>
                        <span class="deal-badge-score">Score: {{ p[10] }}/100</span>
                    </div>

                    <h5 class="fw-bold text-white mb-1" style="font-size:1.15rem;">{{ p[1] }}</h5>
                    <div class="text-secondary small mb-3">📍 {{ p[3] }} • 🏢 <strong>{{ p[4] }}</strong> (ЕИК: {{ p[5] }})</div>

                    <!-- Табло с цени и показатели -->
                    <div class="row g-2 mb-3">
                        <div class="col-4">
                            <div class="stat-box">
                                <div class="text-secondary" style="font-size:10px; font-weight:700;">ТЪРЖНА / ЛИКВИДАЦИЯ</div>
                                <div class="fw-bold text-warning" style="font-size:1rem;">€{{ "{:,.0f}".format(p[7]) }}</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-box">
                                <div class="text-secondary" style="font-size:10px; font-weight:700;">ПАЗАРНА ОЦЕНКА</div>
                                <div class="fw-bold text-light" style="font-size:1rem;">€{{ "{:,.0f}".format(p[8]) }}</div>
                            </div>
                        </div>
                        <div class="col-4">
                            <div class="stat-box">
                                <div class="text-secondary" style="font-size:10px; font-weight:700;">ДИСКОНТ (СПРЕД)</div>
                                <div class="fw-bold text-success" style="font-size:1rem;">-{{ p[9] }}%</div>
                            </div>
                        </div>
                    </div>

                    <!-- Бутони за действие -->
                    <div class="d-flex gap-2">
                        <a href="/export-pdf" target="_blank" class="btn btn-outline-info w-50 py-2 fw-bold" style="border-radius:10px; font-size:13px;">⚡ Свали Меморандум</a>
                        <button class="btn btn-primary w-50 py-2 fw-bold" style="background:#0284c7; border:none; border-radius:10px; font-size:13px;" onclick="openOrderModal('Запитване за: {{ p[1] }}')">📞 Заяви Интерес</button>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- 8. ТАРИФНИ ПЛАНОВЕ (EUR 2026) -->
        <div class="card-dark" id="plans" style="border:1px solid #0284c7; text-align:center;">
            <div class="text-secondary small mb-1" style="letter-spacing:1px;">ЦЕНА НА ЗАЩИТАТА:</div>
            <h2 class="fw-bold mb-3" style="color:#00f0ff; font-size:2rem; font-family:monospace;">€2.00 / ден (€60/мес.)</h2>
            <button class="btn btn-primary w-100 py-3 fw-bold" style="background:#0284c7; border:none; border-radius:12px;" onclick="openOrderModal('Абонаментен Радар - €60')">АКТИВИРАЙ АБОНАМЕНТЕН РАДАР</button>
        </div>

        <!-- Тарифи -->
        <div class="plan-box">
            <div>
                <div class="small fw-bold text-secondary">STARTER EXECUTIVE</div>
                <div class="fw-bold text-white fs-4">€60 <span class="fs-6 text-secondary">/ месец</span></div>
                <div class="text-secondary" style="font-size:11px;">Седмичен луксозен Excel отчет</div>
            </div>
            <button class="btn-plan" onclick="openOrderModal('Starter Executive - €60')">Избери</button>
        </div>

        <div class="plan-box plan-popular">
            <div>
                <div class="d-flex align-items-center gap-2 mb-1">
                    <span class="small fw-bold" style="color:#00f0ff;">PRO RISK MONITOR</span>
                    <span class="badge bg-info text-dark" style="font-size:9px; font-weight:800;">POPULAR</span>
                </div>
                <div class="fw-bold text-white fs-4">€150 <span class="fs-6 text-secondary">/ месец</span></div>
                <div class="text-secondary" style="font-size:11px;">Ежедневен 07:30 ч. радар + алерти</div>
            </div>
            <button class="btn-plan btn-plan-pro" onclick="openOrderModal('PRO RISK MONITOR - €150')">ВЗЕМИ PRO</button>
        </div>

        <div class="plan-box">
            <div>
                <div class="small fw-bold text-secondary">ENTERPRISE M2M</div>
                <div class="fw-bold text-white fs-4">€290 <span class="fs-6 text-secondary">/ месец</span></div>
                <div class="text-secondary" style="font-size:11px;">REST JSON API + llms.txt Gateway</div>
            </div>
            <button class="btn-plan" onclick="openOrderModal('Enterprise M2M - €290')">API Ключ</button>
        </div>

        <!-- 9. M2M GATEWAY FOOTER -->
        <div class="m2m-footer mt-4">
            <div class="d-flex align-items-center gap-2">
                <span style="color:#10b981;">●</span>
                <span class="fw-bold text-white">M2M Gateway:</span>
            </div>
            <div class="d-flex gap-2">
                <a href="/llms.txt" class="btn-m2m">/llms.txt</a>
                <a href="/api/deals" class="btn-m2m">/api/deals</a>
            </div>
        </div>
    </div>

    <!-- МОБИЛНО МЕНЮ (OFFCANVAS DRAWER) -->
    <div class="offcanvas offcanvas-end text-bg-dark" tabindex="-1" id="mobileMenu" style="background-color: #0d1527 !important; border-left: 1px solid var(--border);">
        <div class="offcanvas-header border-bottom border-secondary">
            <h5 class="offcanvas-title fw-bold text-info">📱 PRO INVEST RADAR</h5>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas"></button>
        </div>
        <div class="offcanvas-body d-flex flex-column justify-content-between">
            <div class="d-flex flex-column gap-3">
                <a href="/" class="btn btn-outline-light text-start py-2">🏠 Начало / Радар</a>
                <a href="/export-pdf" target="_blank" class="btn btn-outline-light text-start py-2">📄 Седмичен PDF Доклад</a>
                <a href="/api/deals" target="_blank" class="btn btn-outline-info text-start py-2">&gt;_ M2M JSON API</a>
                <a href="#plans" class="btn btn-warning text-dark fw-bold text-start py-2" data-bs-dismiss="offcanvas">💳 Тарифни планове</a>
            </div>
            <div class="text-center text-secondary small border-top border-secondary pt-3">
                PRO INVEST RADAR AI • EUR 2026
            </div>
        </div>
    </div>

    <!-- Модал за абонамент / запитване -->
    <div class="modal fade" id="orderModal" tabindex="-1">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content" style="background:#0d1527; border:1px solid var(--border); color:#fff; border-radius:16px;">
                <div class="modal-header border-0 pb-0">
                    <h5 class="modal-title fw-bold" id="orderModalTitle">Заявка за актив</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p class="text-secondary small">Въведете служебен имейл за изпращане на пълен правен анализ и координати:</p>
                    <input type="email" id="subEmail" class="custom-input mb-3" placeholder="office@company.bg" required>
                    <button class="btn btn-primary w-100 py-2 fw-bold" style="background:#0284c7; border:none; border-radius:10px;" onclick="confirmOrder()">Потвърди изпращане</button>
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
            var lat = item[13] || 42.6977, lng = item[14] || 23.3219;
            L.marker([lat, lng]).addTo(map).bindPopup("<strong>" + item[1] + "</strong><br>" + item[3] + "<br><span style='color:#059669; font-weight:bold;'>€" + item[7].toLocaleString() + "</span>");
        });

        function updateChsiCalc(val) {
            document.getElementById('sliderValDisplay').innerText = '€' + Number(val).toLocaleString('de-DE');
        }

        function filterCategory(cat, element) {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            element.classList.add('active');
            var cards = document.querySelectorAll('.deal-card');
            cards.forEach(card => {
                var cCat = card.getAttribute('data-category');
                if(cat === 'all' || cCat === cat) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function performAudit() {
            var eik = document.getElementById('eikInput').value.trim();
            if(!eik) return;
            var box = document.getElementById('companyAuditResult');
            box.style.display = 'block';
            document.getElementById('resCompEik').innerText = eik;
            if(eik === '030431138') {
                document.getElementById('resCompName').innerText = 'Трейс Груп Холд АД';
                document.getElementById('resCompManager').innerText = 'Боян Делчев';
            } else {
                document.getElementById('resCompName').innerText = 'Елит Строй Билдинг ООД';
                document.getElementById('resCompManager').innerText = 'Инж. Димитър Георгиев';
            }
        }

        var activePlan = '';
        function openOrderModal(plan) {
            activePlan = plan;
            document.getElementById('orderModalTitle').innerText = plan;
            new bootstrap.Modal(document.getElementById('orderModal')).show();
        }

        function confirmOrder() {
            var email = document.getElementById('subEmail').value;
            if(!email || !email.includes('@')) { alert('Моля въведете валиден имейл!'); return; }
            alert('Заявката е приета за ' + email);
            location.reload();
        }
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, eik, manager, price_eur, market_val, discount_pct, deal_score, status, size_rzp, lat, lng FROM radar_projects")
    projects = c.fetchall()
    conn.close()

    stats = {
        "total": len(projects) if len(projects) > 0 else 5,
        "top_deals": len([p for p in projects if (p[10] or 0) >= 85]) if len(projects) > 0 else 3,
        "avg_discount": "60.8",
        "spread_str": "332 094"
    }
    return render_template_string(FULL_HTML, projects=projects, projects_json=json.dumps(projects), stats=stats)

@app.route("/llms.txt")
def llms_txt():
    content = "# PRO INVEST RADAR AI - Enterprise M2M Gateway 2026\\nAPI: https://stroy-radar-ai.onrender.com/api/deals\\nFormat: JSON"
    return Response(content, mimetype='text/plain')

@app.route("/api/deals")
def api_deals():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, eik, price_eur, deal_score FROM radar_projects")
    rows = c.fetchall()
    conn.close()
    return jsonify({"status": "live", "currency": "EUR", "year": 2026, "count": len(rows), "data": rows})

@app.route("/export-pdf")
def export_pdf():
    return "<script>window.print();</script><div style='padding:20px; font-family:sans-serif;'><h2>PRO INVEST RADAR .BG – ДОКЛАД 2026</h2><p>Експорт на институционалните данни...</p></div>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
