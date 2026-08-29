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
from flask import Flask, request, render_template_string, Response, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "stroy-radar-secret-key-2026")
DB_PATH = "stroy_radar_intel.db"

# --- 1. База данни ---
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

    conn.commit()
    conn.close()

init_db()

# --- 2. Zero-Bounce DNS Валидатор & Имейл ---
def is_email_valid_domain(email):
    try:
        domain = email.split('@')[1]
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False

def send_email_msg(to_email, subject, body_html):
    if not is_email_valid_domain(to_email):
        print(f"[Zero-Bounce] Пропуснат невалиден имейл: {to_email}")
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
    except Exception as e:
        print(f"[!] Грешка при изпращане към {to_email}: {e}")
        return False

# --- 3. B2B Аутрийч Кампания (Партиди по 20) ---
def execute_outreach_batch(batch_size=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, company_name FROM leads_outreach WHERE status = 'pending' LIMIT ?", (batch_size,))
    leads = c.fetchall()
    
    sent_count = 0
    for lead_id, email, company in leads:
        comp_name = company if company else "Колеги"
        subject = f"Нови разрешителни за строеж и търгове за вашия район – Stroy Radar AI"
        body = f"""
        <div style='font-family:Segoe UI, sans-serif; background:#0f172a; color:#f8fafc; padding:25px; border-radius:10px; max-width:600px;'>
            <h2 style='color:#38bdf8; margin-top:0;'>🏗️ Stroy Radar AI</h2>
            <p>Здравейте, {comp_name},</p>
            <p>Платформата за строителен интелиджънс <strong>Stroy Radar AI</strong> следи в реално време новоиздадените разрешителни за строеж и публичните ЧСИ търгове в България.</p>
            <p>Предоставяме ви <strong>7-дневен пълен безплатен тестов достъп</strong>, включващ:</p>
            <ul>
                <li>Ежедневен анализ на новите обекти всяка сутрин в 07:30 ч.</li>
                <li>Директни контакти на инвеститори и възложители</li>
                <li>Интерактивна GIS карта и експорт в Excel</li>
            </ul>
            <p style='margin:25px 0;'>
                <a href='https://stroy-radar-ai.onrender.com' style='background:#2563eb; color:#ffffff; padding:12px 24px; text-decoration:none; border-radius:6px; font-weight:bold; display:inline-block;'>Активирай 7 дни тест безплатно</a>
            </p>
            <p style='font-size:12px; color:#94a3b8; border-top:1px solid #334155; padding-top:15px;'>
                За директна връзка с нас: <a href='mailto:kovko.firma@gmail.com' style='color:#38bdf8;'>kovko.firma@gmail.com</a>
            </p>
        </div>
        """
        if send_email_msg(email, subject, body):
            c.execute("UPDATE leads_outreach SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?", (lead_id,))
            conn.commit()
            sent_count += 1
            time.sleep(2)  # Безопасен интервал между писмата
            
    conn.close()
    return sent_count

# --- 4. Фонов Scheduler за 07:30 ч. ---
def scheduler_loop():
    already_sent = False
    while True:
        try:
            now_bg = datetime.now(ZoneInfo("Europe/Sofia"))
            time_str = now_bg.strftime("%H:%M")
            if time_str == "00:00":
                already_sent = False
            if time_str == "07:30" and not already_sent:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT title, category, location, investor, size_rzp, price_eur FROM radar_projects ORDER BY id DESC LIMIT 3")
                top_items = c.fetchall()
                conn.close()

                items_html = "".join([
                    f"<div style='background:#1e293b; padding:12px; border-radius:6px; margin-bottom:10px; border-left:4px solid #3b82f6;'>"
                    f"<h4 style='color:#ffffff; margin:0;'>{p[0]}</h4>"
                    f"<p style='color:#94a3b8; margin:4px 0 0 0; font-size:13px;'>{p[1]} | {p[2]} | Възложител: {p[3]}</p>"
                    f"</div>" for p in top_items
                ])

                mail_body = f"""
                <div style='font-family:sans-serif; background:#0f172a; color:#f8fafc; padding:20px; border-radius:8px;'>
                    <h2 style='color:#38bdf8;'>Сутрешен Бюлетин ({now_bg.strftime('%d.%m.%Y')})</h2>
                    {items_html}
                    <p><a href='https://stroy-radar-ai.onrender.com' style='background:#2563eb; color:#fff; padding:10px 18px; text-decoration:none; border-radius:6px; display:inline-block;'>Вход в Радара</a></p>
                </div>
                """
                send_email_msg("kovko.firma@gmail.com", f"🏗️ Сутрешен Строителен Радар ({now_bg.strftime('%d.%m.%Y')})", mail_body)
                already_sent = True
            time.sleep(30)
        except Exception:
            time.sleep(60)

threading.Thread(target=scheduler_loop, daemon=True).start()

# --- 5. HTML Шаблони с Viber интеграция ---
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
        .btn-viber { background: #7360f2; color: #fff; font-weight: 600; border-radius: 8px; }
        .btn-viber:hover { background: #5e4bd8; color: #fff; }
        #map { height: 400px; width: 100%; border-radius: 12px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold text-primary" href="/">🏗️ STROY RADAR AI</a>
            <div class="d-flex gap-2">
                <a href="/admin" class="btn btn-outline-warning btn-sm">📊 Админ</a>
                {% if session.get('user_email') %}
                    <a href="/portal" class="btn btn-outline-info btn-sm">👤 Портал</a>
                    <a href="/logout" class="btn btn-outline-danger btn-sm">Изход</a>
                {% else %}
                    <a href="/login" class="btn btn-outline-light btn-sm">Вход</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <div class="row align-items-center g-4 py-3">
            <div class="col-lg-7">
                <span class="badge bg-primary mb-2 px-3 py-2">B2B ConTech Интелиджънс</span>
                <h1 class="display-6 fw-bold text-white mb-3">Мониторинг на нови строежи и ЧСИ имоти</h1>
                <p class="text-secondary lead fs-6">Интерактивна карта, разрешителни за строеж и търгове на парцели в България.</p>
                <div class="d-flex gap-2 mt-3">
                    <a href="mailto:kovko.firma@gmail.com" class="btn btn-outline-light btn-sm">✉️ kovko.firma@gmail.com</a>
                    <a href="viber://chat" class="btn btn-viber btn-sm">💬 Чат във Viber</a>
                </div>
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
                            <input type="text" name="phone" class="form-control bg-dark text-light border-secondary" placeholder="Телефон за връзка" required>
                        </div>
                        <button type="submit" class="btn btn-brand w-100 py-2">Стартирай безплатен тест</button>
                    </form>
                </div>
            </div>
        </div>

        <div class="card card-custom p-4 my-4">
            <h4 class="fw-bold text-white mb-3">🗺️ Интерактивна Карта на Обектите</h4>
            <div id="map"></div>
        </div>

        <div class="card card-custom p-4 my-4">
            <h4 class="fw-bold text-white mb-3">🔍 Обекти и разрешителни на живо</h4>
            <form method="GET" action="/" class="row g-2 mb-3">
                <div class="col-md-5">
                    <input type="text" name="q" class="form-control bg-dark text-light border-secondary" placeholder="Търси по локация, фирма..." value="{{ query }}">
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

    <!-- Футър с контакти -->
    <footer class="border-top border-secondary py-4 mt-5 text-center text-secondary small">
        <div class="container d-flex flex-column flex-md-row justify-content-between align-items-center gap-2">
            <div>© 2026 Stroy Radar AI. Всички права запазени.</div>
            <div class="d-flex gap-3">
                <a href="mailto:kovko.firma@gmail.com" class="text-info text-decoration-none">✉️ kovko.firma@gmail.com</a>
                <a href="viber://chat" class="text-light text-decoration-none">💬 Viber Поддръжка</a>
            </div>
        </div>
    </footer>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 24.5], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);
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
                <a href="viber://chat" class="btn btn-outline-info btn-sm">💬 Помощ във Viber</a>
                <a href="/api/export-leads-csv" class="btn btn-success btn-sm">📥 Свали CSV</a>
                <a href="/logout" class="btn btn-outline-danger btn-sm">Изход</a>
            </div>
        </div>

        <div class="card card-custom p-4 mb-4">
            <h4 class="fw-bold text-white mb-2">⚙️ Персонализирай сутрешния бюлетин (07:30 ч.)</h4>
            <form method="POST" action="/api/update-preferences" class="row g-3">
                <div class="col-md-5">
                    <select name="preferred_region" class="form-select bg-dark text-light border-secondary">
                        <option value="Всички" {% if user_pref[0] == 'Всички' %}selected{% endif %}>Цяла България (Всички)</option>
                        <option value="София" {% if user_pref[0] == 'София' %}selected{% endif %}>София и региона</option>
                        <option value="Пловдив" {% if user_pref[0] == 'Пловдив' %}selected{% endif %}>Пловдив и Тракия</option>
                        <option value="Варна" {% if user_pref[0] == 'Варна' %}selected{% endif %}>Варна и Черноморие</option>
                        <option value="Бургас" {% if user_pref[0] == 'Бургас' %}selected{% endif %}>Бургас и региона</option>
                    </select>
                </div>
                <div class="col-md-5">
                    <select name="preferred_category" class="form-select bg-dark text-light border-secondary">
                        <option value="Всички" {% if user_pref[1] == 'Всички' %}selected{% endif %}>Всички категории</option>
                        <option value="Разрешение за строеж" {% if user_pref[1] == 'Разрешение за строеж' %}selected{% endif %}>Само Разрешителни за строеж</option>
                        <option value="ЧСИ Търг" {% if user_pref[1] == 'ЧСИ Търг' %}selected{% endif %}>Само Търгове от ЧСИ</option>
                        <option value="Промишлено" {% if user_pref[1] == 'Промишлено' %}selected{% endif %}>Само Промишлени бази</option>
                    </select>
                </div>
                <div class="col-md-2">
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
    <title>Админ Панел - Stroy Radar AI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>body { background: #0b0f19; color: #f1f5f9; } .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }</style>
</head>
<body class="p-3 p-md-4">
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h2 class="fw-bold text-warning">📊 Административен Панел & B2B Кампании</h2>
                <small class="text-secondary">Управление на контактите и изпращане на тестови покани</small>
            </div>
            <a href="/" class="btn btn-outline-light btn-sm">← Към сайта</a>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card card-custom p-3 text-center border-primary">
                    <small class="text-secondary">Чакащи B2B Лидове</small>
                    <h2 class="text-primary my-1">{{ pending_leads }}</h2>
                    <a href="/admin/send-outreach-batch" class="btn btn-primary btn-sm mt-2">🚀 Изпрати 20 Покани</a>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card card-custom p-3 text-center border-success">
                    <small class="text-secondary">Изпратени Оферти / Активни</small>
                    <h2 class="text-success my-1">{{ sent_leads }}</h2>
                    <span class="badge bg-success">В процес на конверсия</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card card-custom p-3 text-center border-info">
                    <small class="text-secondary">Обекти в базата</small>
                    <h2 class="text-info my-1">{{ total_projects }}</h2>
                    <span class="badge bg-info text-dark">Реални регистри</span>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card card-custom p-3 text-center border-warning">
                    <small class="text-secondary">Сутрешен График</small>
                    <h3 class="text-warning my-2">07:30 ч.</h3>
                    <span class="badge bg-success">24/7 Активен</span>
                </div>
            </div>
        </div>

        <div class="card card-custom p-4">
            <h4 class="fw-bold text-white mb-3">👥 Списък с B2B контакти и статус на доставката</h4>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>ID</th><th>Фирма</th><th>Имейл</th><th>Статус</th><th>Регион</th></tr>
                    </thead>
                    <tbody>
                        {% for l in leads %}
                        <tr>
                            <td>{{ l[0] }}</td>
                            <td class="fw-bold">{{ l[2] }}</td>
                            <td><code>{{ l[1] }}</code></td>
                            <td>
                                {% if l[4] == 'sent' %}
                                    <span class="badge bg-success">Изпратена покана</span>
                                {% elif l[4] == 'trial_active' %}
                                    <span class="badge bg-warning text-dark">🌟 Активен тест</span>
                                {% else %}
                                    <span class="badge bg-secondary">В очакване</span>
                                {% endif %}
                            </td>
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
    c.execute("SELECT COUNT(*) FROM leads_outreach WHERE status = 'pending'")
    pending_leads = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM leads_outreach WHERE status IN ('sent', 'trial_active')")
    sent_leads = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM radar_projects")
    total_projects = c.fetchone()[0]

    c.execute("SELECT id, email, company_name, phone, status, preferred_region FROM leads_outreach ORDER BY id DESC LIMIT 50")
    leads = c.fetchall()
    conn.close()

    return render_template_string(ADMIN_HTML, pending_leads=pending_leads, sent_leads=sent_leads, total_projects=total_projects, leads=leads)

@app.route("/admin/send-outreach-batch")
def admin_send_batch():
    sent = execute_outreach_batch(20)
    return f"<script>alert('Успешно изпратени {sent} B2B покани за 7-дневен тест с Zero-Bounce валидация!'); window.location.href='/admin';</script>"

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
