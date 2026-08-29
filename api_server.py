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

# --- 1. База данни с координати (lat/lng) ---
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

    # Проверка дали съществуват координатни колони
    try:
        c.execute("ALTER TABLE radar_projects ADD COLUMN lat REAL DEFAULT 42.6977")
        c.execute("ALTER TABLE radar_projects ADD COLUMN lng REAL DEFAULT 23.3219")
    except Exception:
        pass

    # Зареждане на гео-реферирани обекти
    c.execute("SELECT COUNT(*) FROM radar_projects")
    if c.fetchone()[0] == 0:
        seed_projects = [
            ("Многофамилна жилищна сграда с подземни гаражи", "Разрешение за строеж", "гр. София, кв. Малинова Долина", "Инвест Билд София ООД", "4 850 кв.м", 0, "Издадено РС", 42.6366, 23.3448),
            ("Логистичен и складов център за промишлени стоки", "Промишлено", "с. Равно Поле, общ. Елин Пелин", "Логистикс Парк АД", "12 400 кв.м", 0, "Одобрен проект", 42.6712, 23.5284),
            ("УПИ за жилищно строителство на публична продан", "ЧСИ Търг", "гр. Пловдив, р-н Тракия", "ЧСИ Рег. №824", "2 150 кв.м", 185000.0, "Търг до 15.09", 42.1354, 24.7876),
            ("Жилищен комплекс от затворен тип (Фаза 1)", "Разрешение за строеж", "гр. Варна, кв. Бриз", "Черноморие Девелъпмънт", "8 200 кв.м", 0, "В строеж", 43.2189, 27.9542),
            ("Парцел за складова база с лице на главен път", "ЧСИ Търг", "гр. Бургас, Северна промишлена зона", "ЧСИ Рег. №712", "5 600 кв.м", 120000.0, "Търг до 22.09", 42.5224, 27.4475),
            ("Нова административна сграда с шоурум", "Разрешение за строеж", "гр. София, бул. Цариградско шосе", "Тракия Кепитъл ЕООД", "6 300 кв.м", 0, "Издадено РС", 42.6588, 23.3821),
            ("Парцел за жилищно застрояване - ЧСИ", "ЧСИ Търг", "гр. София, кв. Овча Купел", "ЧСИ Рег. №838", "1 820 кв.м", 210000.0, "Търг до 30.09", 42.6745, 23.2563),
            ("Производствена база за метални елементи", "Промишлено", "гр. Пловдив, Индустриална Зона Тракия", "Метал Строй АД", "9 100 кв.м", 0, "Строителен надзор", 42.1211, 24.8105)
        ]
        c.executemany("INSERT INTO radar_projects (title, category, location, investor, size_rzp, price_eur, status, lat, lng) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", seed_projects)

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

# --- 3. Фонов Scheduler (07:30 ч.) ---
def background_scheduler():
    already_sent_today = False
    while True:
        try:
            now_bg = datetime.now(ZoneInfo("Europe/Sofia"))
            time_str = now_bg.strftime("%H:%M")

            if time_str == "00:00":
                already_sent_today = False

            if time_str == "07:30" and not already_sent_today:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT title, category, location, investor, size_rzp, price_eur FROM radar_projects ORDER BY id DESC LIMIT 3")
                top_items = c.fetchall()
                conn.close()

                tg_msg = f"🌅 <b>Сутрешен Строителен Радар ({now_bg.strftime('%d.%m.%Y')})</b>\n\n"
                items_html = ""
                for p in top_items:
                    price_str = f"€{p[5]:,.0f}" if p[5] > 0 else p[4]
                    tg_msg += f"🏗️ <b>{p[0]}</b>\n📍 {p[2]}\n👤 {p[3]} ({price_str})\n\n"
                    items_html += f"<div style='background:#1e293b; padding:10px; border-radius:6px; margin-bottom:8px;'><strong>{p[0]}</strong><br><small>{p[1]} | {p[2]} | {p[3]}</small></div>"

                send_telegram_alert(tg_msg)
                send_email_msg("kovko.firma@gmail.com", f"🏗️ Сутрешен Строителен Радар ({now_bg.strftime('%d.%m.%Y')})", f"<div style='font-family:sans-serif; background:#0f172a; color:#fff; padding:20px;'><h3>Сутрешен Бюлетин:</h3>{items_html}</div>")
                already_sent_today = True

            time.sleep(30)
        except Exception:
            time.sleep(60)

threading.Thread(target=background_scheduler, daemon=True).start()

# --- 4. HTML Шаблони с Интерактивна Карта (Leaflet) ---
MAIN_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stroy Radar AI - ConTech Платформа & Интерактивна Карта</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }
        .btn-brand { background: #2563eb; color: #fff; font-weight: 600; border-radius: 8px; }
        .btn-brand:hover { background: #1d4ed8; color: #fff; }
        #map { height: 420px; width: 100%; border-radius: 12px; border: 1px solid #374151; z-index: 1; }
        .leaflet-popup-content-wrapper { background: #1e293b; color: #fff; border-radius: 8px; }
        .leaflet-popup-tip { background: #1e293b; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold text-primary" href="/">🏗️ STROY RADAR AI</a>
            <div class="d-flex gap-2">
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
        <!-- Регистрационен блок -->
        <div class="row align-items-center g-4 py-3">
            <div class="col-lg-7">
                <span class="badge bg-primary mb-2 px-3 py-2">B2B ConTech Интелиджънс</span>
                <h1 class="display-6 fw-bold text-white mb-3">Мониторинг на строежи и ЧСИ имоти в реално време</h1>
                <p class="text-secondary lead fs-6">Интерактивна сателитна карта и база данни за новоиздадени разрешителни за строеж и търгове в България.</p>
                <div class="row g-2 text-light small">
                    <div class="col-6">✓ Интерактивна GIS карта</div>
                    <div class="col-6">✓ Telegram Push известия</div>
                    <div class="col-6">✓ Ежедневен бюлетин в 07:30 ч.</div>
                    <div class="col-6">✓ Експорт в Excel (CSV)</div>
                </div>
            </div>
            <div class="col-lg-5">
                <div class="card card-custom p-4 shadow-lg">
                    <h4 class="fw-bold mb-3 text-white text-center">Активирай 7 дни тест</h4>
                    <form action="/api/register-trial" method="POST">
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Фирма / Инвеститор</label>
                            <input type="text" name="company" class="form-control bg-dark text-light border-secondary" placeholder="Име на фирмата" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Имейл адрес</label>
                            <input type="email" name="email" class="form-control bg-dark text-light border-secondary" placeholder="office@company.bg" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Телефон</label>
                            <input type="text" name="phone" class="form-control bg-dark text-light border-secondary" placeholder="0888 123 456" required>
                        </div>
                        <button type="submit" class="btn btn-brand w-100 py-2">Стартирай безплатен тест</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- GIS Интерактивна Карта -->
        <div class="card card-custom p-4 my-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h4 class="fw-bold text-white mb-0">🗺️ Интерактивна Карта на Обектите</h4>
                    <small class="text-secondary">Кликнете върху маркер за детайли на обекта и инвеститора</small>
                </div>
                <span class="badge bg-success">Карта на живо</span>
            </div>
            <div id="map"></div>
        </div>

        <!-- Търсене и филтри -->
        <div class="card card-custom p-4 my-4">
            <h4 class="fw-bold text-white mb-3">🔍 Списък и търсене на обекти</h4>
            <form method="GET" action="/" class="row g-3">
                <div class="col-md-5">
                    <input type="text" name="q" class="form-control bg-dark text-light border-secondary" placeholder="Търси по ключова дума, инвеститор..." value="{{ query }}">
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

            <div class="table-responsive mt-4">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small">
                            <th>Обект</th><th>Категория</th><th>Локация</th><th>Възложител</th><th>Параметри / Цена</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in projects %}
                        <tr>
                            <td class="fw-bold text-white">{{ p[1] }}</td>
                            <td>
                                {% if 'ЧСИ' in p[2] %}
                                    <span class="badge bg-warning text-dark">{{ p[2] }}</span>
                                {% else %}
                                    <span class="badge bg-info text-dark">{{ p[2] }}</span>
                                {% endif %}
                            </td>
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

    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 24.5], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);

        var projectsData = {{ projects_json | safe }};
        projectsData.forEach(function(item) {
            var lat = item[8] || 42.6977;
            var lng = item[9] || 23.3219;
            var priceOrSize = item[6] > 0 ? "€" + item[6].toLocaleString() : item[5];

            var popupContent = "<div style='font-size:13px;'>" +
                "<strong style='color:#38bdf8;'>" + item[1] + "</strong><br>" +
                "<b>Категория:</b> " + item[2] + "<br>" +
                "<b>Локация:</b> " + item[3] + "<br>" +
                "<b>Възложител:</b> " + item[4] + "<br>" +
                "<b>Параметри:</b> " + priceOrSize +
                "</div>";

            L.marker([lat, lng]).addTo(map).bindPopup(popupContent);
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
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background: #0b0f19; color: #f1f5f9; }
        .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }
        #portal-map { height: 350px; width: 100%; border-radius: 12px; }
    </style>
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

        <div class="card card-custom p-4 mb-4">
            <h5 class="fw-bold text-white mb-3">🗺️ Карта на обектите за абонати</h5>
            <div id="portal-map"></div>
        </div>

        <div class="card card-custom p-4">
            <h4 class="fw-bold text-white mb-3">Всички обекти в реално време</h4>
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
        var map = L.map('portal-map').setView([42.6977, 24.5], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        var projectsData = {{ projects_json | safe }};
        projectsData.forEach(function(item) {
            var lat = item[8] || 42.6977;
            var lng = item[9] || 23.3219;
            var priceOrSize = item[6] > 0 ? "€" + item[6].toLocaleString() : item[5];

            var popupContent = "<div style='font-size:13px; color:#000;'>" +
                "<strong>" + item[1] + "</strong><br>" +
                "Локация: " + item[3] + "<br>" +
                "Възложител: " + item[4] + "<br>" +
                "Параметри: " + priceOrSize +
                "</div>";

            L.marker([lat, lng]).addTo(map).bindPopup(popupContent);
        });
    </script>
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
        q_wildcard = f"%{query}%"
        params.extend([q_wildcard, q_wildcard, q_wildcard])

    if category:
        sql += " AND category = ?"
        params.append(category)

    sql += " ORDER BY id DESC"
    c.execute(sql, params)
    projects = c.fetchall()
    conn.close()

    return render_template_string(
        MAIN_HTML,
        projects=projects,
        projects_json=json.dumps(projects),
        query=query,
        category=category
    )

@app.route("/portal")
def portal():
    if "user_email" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, size_rzp, price_eur, status, lat, lng FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()

    return render_template_string(
        PORTAL_HTML,
        user_email=session["user_email"],
        projects=projects,
        projects_json=json.dumps(projects)
    )

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

    send_telegram_alert(f"🌟 <b>Нов абонат (7 дни тест)!</b>\nФирма: {company}\nИмейл: {email}\nТел: {phone}")
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
