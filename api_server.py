import os
import io
import csv
import json
import sqlite3
import smtplib
import socket
import urllib.request
import urllib.parse
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, render_template_string, Response, session, redirect, url_for, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "stroy-radar-secret-key-2026")
DB_PATH = "stroy_radar_intel.db"

# --- 1. База данни с потребителски настройки ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads_outreach (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            company_name TEXT,
            phone TEXT,
            status TEXT DEFAULT 'pending',
            preferred_region TEXT DEFAULT 'Всички',
            preferred_category TEXT DEFAULT 'Всички',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP,
            trial_start TIMESTAMP,
            last_followup_day INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS radar_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            location TEXT,
            investor TEXT,
            size_rzp TEXT,
            price_eur REAL,
            status TEXT,
            lat REAL DEFAULT 42.6977,
            lng REAL DEFAULT 23.3219,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Миграция за нови колони при нужда
    try:
        c.execute("ALTER TABLE leads_outreach ADD COLUMN preferred_region TEXT DEFAULT 'Всички'")
        c.execute("ALTER TABLE leads_outreach ADD COLUMN preferred_category TEXT DEFAULT 'Всички'")
    except Exception:
        pass

    conn.commit()
    conn.close()

init_db()

# --- 2. Валидация и Известия ---
def is_email_valid_domain(email):
    try:
        domain = email.split('@')[1]
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False

def send_telegram_alert(message_text):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not bot_token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = json.dumps({"chat_id": chat_id, "text": message_text, "parse_mode": "HTML"}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False

def send_email_msg(to_email, subject, body_html):
    if not is_email_valid_domain(to_email):
        return False
    sender = os.environ.get("SENDER_EMAIL", "kovko.firma@gmail.com")
    password = os.environ.get("SENDER_APP_PASSWORD", "")
    if not password:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"Stroy Radar AI <{sender}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        return True
    except Exception:
        return False

# --- 3. Персонализиран сутрешен бюлетин в 07:30 ч. ---
def send_custom_morning_digests():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT email, company_name, preferred_region, preferred_category FROM leads_outreach WHERE status = 'trial_active'")
    subscribers = c.fetchall()
    
    now_bg = datetime.now(ZoneInfo("Europe/Sofia")).strftime("%d.%m.%Y")

    for email, company, pref_reg, pref_cat in subscribers:
        sql = "SELECT title, category, location, investor, size_rzp, price_eur FROM radar_projects WHERE 1=1"
        params = []
        if pref_reg and pref_reg != "Всички":
            sql += " AND location LIKE ?"
            params.append(f"%{pref_reg}%")
        if pref_cat and pref_cat != "Всички":
            sql += " AND category = ?"
            params.append(pref_cat)
        sql += " ORDER BY id DESC LIMIT 3"
        
        c.execute(sql, params)
        matched_projects = c.fetchall()
        
        if not matched_projects:
            c.execute("SELECT title, category, location, investor, size_rzp, price_eur FROM radar_projects ORDER BY id DESC LIMIT 3")
            matched_projects = c.fetchall()

        items_html = "".join([
            f"<div style='background:#1e293b; padding:12px; border-radius:6px; margin-bottom:10px; border-left:4px solid #3b82f6;'>"
            f"<h4 style='color:#ffffff; margin:0;'>{p[0]}</h4>"
            f"<p style='color:#94a3b8; margin:4px 0 0 0; font-size:13px;'>{p[1]} | {p[2]} | Възложител: {p[3]}</p>"
            f"</div>" for p in matched_projects
        ])

        mail_body = f"""
        <div style='font-family:sans-serif; background:#0f172a; color:#f8fafc; padding:20px; border-radius:8px;'>
            <h2 style='color:#38bdf8;'>Персонален Сутрешен Бюлетин ({now_bg})</h2>
            <p style='color:#94a3b8;'>Здравейте, <strong>{company}</strong>. Ето най-новите обекти съобразени с вашите филтри ({pref_reg} / {pref_cat}):</p>
            {items_html}
            <p><a href='https://stroy-radar-ai.onrender.com/portal' style='background:#2563eb; color:#fff; padding:10px 18px; text-decoration:none; border-radius:6px; display:inline-block;'>Вход в Личния Портал</a></p>
        </div>
        """
        send_email_msg(email, f"🏗️ Вашите нови строителни обекти за деня ({now_bg})", mail_body)

    # Административно известие
    send_email_msg("kovko.firma@gmail.com", f"📊 Сутрешни бюлетини изпратени успешно ({now_bg})", f"<p>Обработени и изпратени персонални отчети до всички активни потребители.</p>")
    conn.close()

def scheduler_loop():
    already_sent = False
    while True:
        try:
            now_bg = datetime.now(ZoneInfo("Europe/Sofia"))
            time_str = now_bg.strftime("%H:%M")
            if time_str == "00:00":
                already_sent = False
            if time_str == "07:30" and not already_sent:
                send_custom_morning_digests()
                already_sent = True
            time.sleep(30)
        except Exception:
            time.sleep(60)

threading.Thread(target=scheduler_loop, daemon=True).start()

# --- 4. HTML Шаблони ---
MAIN_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stroy Radar AI - Строителен & ЧСИ Мониторинг</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }
        .btn-brand { background: #2563eb; color: #fff; font-weight: 600; border-radius: 8px; }
        #map { height: 400px; width: 100%; border-radius: 12px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold text-primary" href="/">🏗️ STROY RADAR AI</a>
            <div class="d-flex gap-2">
                <a href="/admin" class="btn btn-outline-warning btn-sm">📊 Админ Табло</a>
                {% if session.get('user_email') %}
                    <a href="/portal" class="btn btn-outline-info btn-sm">👤 Клиентски Портал</a>
                    <a href="/logout" class="btn btn-outline-danger btn-sm">Изход</a>
                {% else %}
                    <a href="/login" class="btn btn-outline-light btn-sm">Вход</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <!-- Регистрация -->
        <div class="row align-items-center g-4 py-3">
            <div class="col-lg-7">
                <span class="badge bg-primary mb-2 px-3 py-2">B2B ConTech Интелиджънс</span>
                <h1 class="display-6 fw-bold text-white mb-3">Мониторинг на нови строежи и ЧСИ имоти</h1>
                <p class="text-secondary lead fs-6">Интерактивна карта, разрешителни за строеж и търгове на парцели в България.</p>
            </div>
            <div class="col-lg-5">
                <div class="card card-custom p-4 shadow-lg">
                    <h4 class="fw-bold mb-3 text-white text-center">Активирай 7 дни тест</h4>
                    <form action="/api/register-trial" method="POST">
                        <div class="mb-2">
                            <input type="text" name="company" class="form-control bg-dark text-light border-secondary" placeholder="Фирма / Инвеститор" required>
                        </div>
                        <div class="mb-2">
                            <input type="email" name="email" class="form-control bg-dark text-light border-secondary" placeholder="office@company.bg" required>
                        </div>
                        <div class="mb-3">
                            <input type="text" name="phone" class="form-control bg-dark text-light border-secondary" placeholder="Телефон за контакт" required>
                        </div>
                        <button type="submit" class="btn btn-brand w-100 py-2">Стартирай безплатен тест</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- GIS Карта -->
        <div class="card card-custom p-4 my-4">
            <h4 class="fw-bold text-white mb-3">🗺️ Интерактивна Карта на Обектите</h4>
            <div id="map"></div>
        </div>

        <!-- Търсене и филтри -->
        <div class="card card-custom p-4 my-4">
            <h4 class="fw-bold text-white mb-3">🔍 Обекти и разрешителни на живо</h4>
            <form method="GET" action="/" class="row g-2 mb-3">
                <div class="col-md-5">
                    <input type="text" name="q" class="form-control bg-dark text-light border-secondary" placeholder="Търси по квартал, фирма..." value="{{ query }}">
                </div>
                <div class="col-md-4">
                    <select name="category" class="form-select bg-dark text-light border-secondary">
                        <option value="">Всички категории</option>
                        <option value="Разрешение за строеж" {% if category == 'Разрешение за строеж' %}selected{% endif %}>Разрешение за строеж</option>
                        <option value="ЧСИ Търг" {% if category == 'ЧСИ Търг' %}selected{% endif %}>ЧСИ Търгове</option>
                        <option value="Промишлено" {% if category == 'Промишлено' %}selected{% endif %}>Промишлено строителство</option>
                    </select>
                </div>
                <div class="col-md-3 d-flex gap-2">
                    <button type="submit" class="btn btn-primary w-100">Филтрирай</button>
                    <a href="/" class="btn btn-outline-secondary">Изчисти</a>
                </div>
            </form>

            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>Обект</th><th>Категория</th><th>Локация</th><th>Възложител</th><th>Параметри / Цена</th></tr>
                    </thead>
                    <tbody>
                        {% for p in projects %}
                        <tr>
                            <td class="fw-bold text-white">{{ p[1] }}</td>
                            <td><span class="badge bg-secondary">{{ p[2] }}</span></td>
                            <td>{{ p[3] }}</td>
                            <td class="text-info">{{ p[4] }}</td>
                            <td>{{ "€{:,.0f}".format(p[6]) if p[6] > 0 else p[5] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 24.5], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        var projectsData = {{ projects_json | safe }};
        projectsData.forEach(function(item) {
            var lat = item[8] || 42.6977;
            var lng = item[9] || 23.3219;
            var priceOrSize = item[6] > 0 ? "€" + item[6].toLocaleString() : item[5];
            L.marker([lat, lng]).addTo(map).bindPopup("<strong>" + item[1] + "</strong><br>" + item[3] + "<br>" + priceOrSize);
        });
    </script>
</body>
</html>
"""

PORTAL_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Клиентски Портал - Stroy Radar AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { background: #0b0f19; color: #f1f5f9; } .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }</style>
</head>
<body class="p-3 p-md-4">
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h2 class="fw-bold">👤 Клиентски Портал: {{ user_email }}</h2>
                <span class="badge bg-success">7-дневен тест активен</span>
            </div>
            <div class="d-flex gap-2">
                <a href="/api/export-leads-csv" class="btn btn-success btn-sm">📥 Свали Excel (CSV)</a>
                <a href="/logout" class="btn btn-outline-danger btn-sm">Изход</a>
            </div>
        </div>

        <!-- Настройка на личните предпочитания за бюлетина -->
        <div class="card card-custom p-4 mb-4">
            <h4 class="fw-bold text-white mb-2">⚙️ Персонализирай сутрешния бюлетин (07:30 ч.)</h4>
            <p class="text-secondary small">Изберете за кои региони и типове обекти искате да получавате приоритетни известия всяка сутрин.</p>
            <form method="POST" action="/api/update-preferences" class="row g-3">
                <div class="col-md-5">
                    <label class="form-label text-secondary small">Предпочитан регион:</label>
                    <select name="preferred_region" class="form-select bg-dark text-light border-secondary">
                        <option value="Всички" {% if user_pref[0] == 'Всички' %}selected{% endif %}>Цяла България (Всички)</option>
                        <option value="София" {% if user_pref[0] == 'София' %}selected{% endif %}>София и региона</option>
                        <option value="Пловдив" {% if user_pref[0] == 'Пловдив' %}selected{% endif %}>Пловдив и Тракия</option>
                        <option value="Варна" {% if user_pref[0] == 'Варна' %}selected{% endif %}>Варна и Черноморие</option>
                        <option value="Бургас" {% if user_pref[0] == 'Бургас' %}selected{% endif %}>Бургас и региона</option>
                    </select>
                </div>
                <div class="col-md-5">
                    <label class="form-label text-secondary small">Категория обекти:</label>
                    <select name="preferred_category" class="form-select bg-dark text-light border-secondary">
                        <option value="Всички" {% if user_pref[1] == 'Всички' %}selected{% endif %}>Всички категории</option>
                        <option value="Разрешение за строеж" {% if user_pref[1] == 'Разрешение за строеж' %}selected{% endif %}>Само Разрешителни за строеж</option>
                        <option value="ЧСИ Търг" {% if user_pref[1] == 'ЧСИ Търг' %}selected{% endif %}>Само Търгове от ЧСИ</option>
                        <option value="Промишлено" {% if user_pref[1] == 'Промишлено' %}selected{% endif %}>Само Промишлени бази</option>
                    </select>
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary w-100">Запази</button>
                </div>
            </form>
        </div>

        <div class="card card-custom p-4">
            <h4 class="fw-bold text-white mb-3">Обекти в реално време</h4>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>Обект</th><th>Категория</th><th>Локация</th><th>Възложител</th><th>Параметри / Цена</th></tr>
                    </thead>
                    <tbody>
                        {% for p in projects %}
                        <tr>
                            <td class="fw-bold text-white">{{ p[1] }}</td>
                            <td><span class="badge bg-secondary">{{ p[2] }}</span></td>
                            <td>{{ p[3] }}</td>
                            <td class="text-info">{{ p[4] }}</td>
                            <td>{{ "€{:,.0f}".format(p[6]) if p[6] > 0 else p[5] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Админ Аналитичен Панел - Stroy Radar AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { background: #0b0f19; color: #f1f5f9; } .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }</style>
</head>
<body class="p-3 p-md-4">
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h2 class="fw-bold text-warning">📊 Административен Панел & KPI Метрики</h2>
                <small class="text-secondary">Управление на системните ресурси и B2B кампаниите</small>
            </div>
            <a href="/" class="btn btn-outline-light btn-sm">← Към сайта</a>
        </div>

        <!-- KPI Метрики -->
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card card-custom p-3 text-center border-primary">
                    <small class="text-secondary">B2B База Контакти</small>
                    <h2 class="text-primary my-1">{{ total_leads }}</h2>
                    <span class="badge bg-primary-subtle text-primary">Готови за кампания</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card card-custom p-3 text-center border-success">
                    <small class="text-secondary">Активни 7-дни Тестове</small>
                    <h2 class="text-success my-1">{{ active_trials }}</h2>
                    <span class="badge bg-success">Реални потребители</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card card-custom p-3 text-center border-info">
                    <small class="text-secondary">Строителни Обекти в Радара</small>
                    <h2 class="text-info my-1">{{ total_projects }}</h2>
                    <span class="badge bg-info text-dark">Регистри по ЗУТ & ЧСИ</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card card-custom p-3 text-center border-warning">
                    <small class="text-secondary">Фонов График (Scheduler)</small>
                    <h3 class="text-warning my-2">07:30 ч.</h3>
                    <span class="badge bg-success">24/7 Активен</span>
                </div>
            </div>
        </div>

        <!-- Добавяне на нов обект -->
        <div class="card card-custom p-4 mb-4">
            <h4 class="fw-bold text-white mb-3">➕ Ръчно добавяне на нов строителен обект или търг</h4>
            <form method="POST" action="/admin/add-project" class="row g-2">
                <div class="col-md-4">
                    <input type="text" name="title" class="form-control bg-dark text-light border-secondary" placeholder="Заглавие на обекта" required>
                </div>
                <div class="col-md-3">
                    <select name="category" class="form-select bg-dark text-light border-secondary">
                        <option value="Разрешение за строеж">Разрешение за строеж</option>
                        <option value="ЧСИ Търг">ЧСИ Търг</option>
                        <option value="Промишлено">Промишлено строителство</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <input type="text" name="location" class="form-control bg-dark text-light border-secondary" placeholder="Локация (напр. гр. София, кв. Изток)" required>
                </div>
                <div class="col-md-2">
                    <input type="text" name="investor" class="form-control bg-dark text-light border-secondary" placeholder="Възложител / ЧСИ" required>
                </div>
                <div class="col-md-3 mt-2">
                    <input type="text" name="size_rzp" class="form-control bg-dark text-light border-secondary" placeholder="РЗП (напр. 3 500 кв.м)">
                </div>
                <div class="col-md-3 mt-2">
                    <input type="number" step="1000" name="price_eur" class="form-control bg-dark text-light border-secondary" placeholder="Цена в € (ако е ЧСИ търг)" value="0">
                </div>
                <div class="col-md-6 mt-2">
                    <button type="submit" class="btn btn-success w-100">Добави в Радара</button>
                </div>
            </form>
        </div>

        <!-- Таблица с потребители -->
        <div class="card card-custom p-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="fw-bold text-white mb-0">👥 Всички регистрирани потребители и филтри</h4>
                <a href="/api/export-leads-csv" class="btn btn-success btn-sm">📥 Свали CSV</a>
            </div>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>ID</th><th>Фирма</th><th>Имейл</th><th>Телефон</th><th>Статус</th><th>Регион филтър</th></tr>
                    </thead>
                    <tbody>
                        {% for l in leads %}
                        <tr>
                            <td>{{ l[0] }}</td>
                            <td class="fw-bold">{{ l[2] }}</td>
                            <td><code>{{ l[1] }}</code></td>
                            <td>{{ l[3] if l[3] else '—' }}</td>
                            <td><span class="badge bg-info text-dark">{{ l[4] }}</span></td>
                            <td>{{ l[5] }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Вход</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body style="background:#0b0f19; color:#fff; display:flex; align-items:center; justify-content:center; min-height:100vh;">
    <div class="p-4" style="background:#111827; border:1px solid #1f2937; border-radius:12px; width:100%; max-width:400px;">
        <h3 class="mb-3 text-center">Вход в Stroy Radar</h3>
        <form method="POST">
            <div class="mb-3">
                <label class="form-label text-secondary small">Имейл адрес:</label>
                <input type="email" name="email" class="form-control bg-dark text-light border-secondary" placeholder="office@company.com" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Вход</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    sql = "SELECT id, title, category, location, investor, size_rzp, price_eur, status, lat, lng FROM radar_projects WHERE 1=1"
    params = []
    if query:
        sql += " AND (title LIKE ? OR location LIKE ? OR investor LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%"])
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY id DESC"
    c.execute(sql, params)
    projects = c.fetchall()
    conn.close()

    return render_template_string(MAIN_HTML, projects=projects, projects_json=json.dumps(projects), query=query, category=category)

@app.route("/portal")
def portal():
    if "user_email" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT preferred_region, preferred_category FROM leads_outreach WHERE email = ?", (session["user_email"],))
    row = c.fetchone()
    user_pref = row if row else ("Всички", "Всички")

    c.execute("SELECT id, title, category, location, investor, size_rzp, price_eur, status FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()

    return render_template_string(PORTAL_HTML, user_email=session["user_email"], user_pref=user_pref, projects=projects)

@app.route("/api/update-preferences", methods=["POST"])
def update_preferences():
    if "user_email" not in session:
        return redirect(url_for("login"))

    pref_reg = request.form.get("preferred_region", "Всички")
    pref_cat = request.form.get("preferred_category", "Всички")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE leads_outreach SET preferred_region = ?, preferred_category = ? WHERE email = ?", (pref_reg, pref_cat, session["user_email"]))
    conn.commit()
    conn.close()

    return redirect(url_for("portal"))

@app.route("/admin")
def admin_panel():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM leads_outreach")
    total_leads = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM leads_outreach WHERE status = 'trial_active'")
    active_trials = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM radar_projects")
    total_projects = c.fetchone()[0]

    c.execute("SELECT id, email, company_name, phone, status, preferred_region FROM leads_outreach ORDER BY id DESC LIMIT 50")
    leads = c.fetchall()
    conn.close()

    return render_template_string(ADMIN_HTML, total_leads=total_leads, active_trials=active_trials, total_projects=total_projects, leads=leads)

@app.route("/admin/add-project", methods=["POST"])
def admin_add_project():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    location = request.form.get("location", "").strip()
    investor = request.form.get("investor", "").strip()
    size_rzp = request.form.get("size_rzp", "").strip()
    price_eur = float(request.form.get("price_eur", 0) or 0)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO radar_projects (title, category, location, investor, size_rzp, price_eur, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Издадено РС')
    """, (title, category, location, investor, size_rzp, price_eur))
    conn.commit()
    conn.close()

    send_telegram_alert(f"🏗️ <b>Нов добавен обект в Радара!</b>\n{title}\n📍 {location}\n👤 {investor}")
    return redirect(url_for("admin_panel"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        session["user_email"] = email
        return redirect(url_for("portal"))
    return render_template_string(LOGIN_HTML)

@app.route("/logout")
def logout():
    session.pop("user_email", None)
    return redirect(url_for("home"))

@app.route("/api/register-trial", methods=["POST"])
def register_trial():
    company = request.form.get("company", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not is_email_valid_domain(email):
        return "<script>alert('Грешка: Невалиден имейл домейн!'); window.history.back();</script>"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO leads_outreach (email, company_name, phone, status, trial_start, sent_at) 
        VALUES (?, ?, ?, 'trial_active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(email) DO UPDATE SET 
            company_name=excluded.company_name,
            phone=excluded.phone,
            status='trial_active',
            trial_start=CURRENT_TIMESTAMP
    """, (email, company, phone))
    conn.commit()
    conn.close()

    send_telegram_alert(f"🌟 <b>Нова активация (7 дни тест)!</b>\nФирма: {company}\nИмейл: {email}\nТел: {phone}")
    session["user_email"] = email
    return redirect(url_for("portal"))

@app.route("/api/export-leads-csv")
def export_leads():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, size_rzp, price_eur FROM radar_projects ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["ID", "Обект", "Категория", "Локация", "Инвеститор", "РЗП/Площ", "Цена (€)"])
    for r in rows:
        writer.writerow(r)

    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=stroy_radar_projects.csv"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
