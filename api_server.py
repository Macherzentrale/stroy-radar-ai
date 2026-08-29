import os
import io
import csv
import json
import sqlite3
import smtplib
import socket
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

# --- 1. База данни с Lead Scoring ---
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
            score INTEGER DEFAULT 0,
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

    c.execute('''
        CREATE TABLE IF NOT EXISTS project_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            project_title TEXT,
            applicant_company TEXT,
            applicant_email TEXT,
            applicant_phone TEXT,
            service_type TEXT,
            message TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

init_db()

def add_lead_score(email, points):
    if not email:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE leads_outreach SET score = score + ? WHERE email = ?", (points, email))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Lead Score Error] {e}")

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
        print(f"[!] SMTP грешка: {e}")
        return False

# --- 3. Автоматична B2B Аутрийч Кампания (Партиди по 20) ---
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
                За връзка с нас: <a href='mailto:kovko.firma@gmail.com' style='color:#38bdf8;'>kovko.firma@gmail.com</a>
            </p>
        </div>
        """
        if send_email_msg(email, subject, body):
            c.execute("UPDATE leads_outreach SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?", (lead_id,))
            conn.commit()
            sent_count += 1
            time.sleep(2)
            
    conn.close()
    return sent_count

# --- 4. Напълно автономен 24/7 Scheduler ---
def background_scheduler():
    already_sent_digest = False
    already_sent_outreach = False
    
    while True:
        try:
            now_bg = datetime.now(ZoneInfo("Europe/Sofia"))
            time_str = now_bg.strftime("%H:%M")

            if time_str == "00:00":
                already_sent_digest = False
                already_sent_outreach = False

            # В 07:30 ч. -> Изпращане на сутрешния бюлетин
            if time_str == "07:30" and not already_sent_digest:
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
                already_sent_digest = True

            # В 08:00 ч. -> Автоматично изпращане на 20 B2B покани
            if time_str == "08:00" and not already_sent_outreach:
                sent_total = execute_outreach_batch(20)
                if sent_total > 0:
                    send_email_msg(
                        "kovko.firma@gmail.com",
                        f"🚀 Автономен B2B Аутрийч: Изпратени {sent_total} покани",
                        f"<p>Днес в 08:00 ч. системата автоматично обработи и изпрати покани към {sent_total} фирми с Zero-Bounce валидация.</p>"
                    )
                already_sent_outreach = True

            time.sleep(30)
        except Exception:
            time.sleep(60)

threading.Thread(target=background_scheduler, daemon=True).start()

# --- 5. HTML Шаблони ---
MAIN_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stroy Radar AI – Мониторинг на строежи и ЧСИ имоти</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }
        .btn-brand { background: #2563eb; color: #fff; font-weight: 600; border-radius: 8px; }
        .btn-brand:hover { background: #1d4ed8; color: #fff; }
        .btn-viber { background: #7360f2; color: #fff; font-weight: 600; border-radius: 8px; }
        .btn-viber:hover { background: #5e4bd8; color: #fff; }
        #map { height: 380px; width: 100%; border-radius: 12px; }
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

    <main class="container py-4">
        <div class="row align-items-center g-4 py-3">
            <div class="col-lg-7">
                <span class="badge bg-primary mb-2 px-3 py-2">B2B ConTech Интелиджънс</span>
                <h1 class="display-6 fw-bold text-white mb-3">Мониторинг на нови строежи и ЧСИ имоти</h1>
                <p class="text-secondary lead fs-6">Интерактивна сателитна карта, разрешителни за строеж и търгове на парцели в реално време.</p>
                <div class="d-flex gap-2 mt-3">
                    <a href="mailto:kovko.firma@gmail.com" class="btn btn-outline-light btn-sm">✉️ kovko.firma@gmail.com</a>
                    <a href="viber://chat" class="btn btn-viber btn-sm">💬 Viber Чат</a>
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

        <section class="card card-custom p-4 my-4">
            <h4 class="fw-bold text-white mb-3">🗺️ Интерактивна Карта на Обектите</h4>
            <div id="map"></div>
        </section>

        <section class="card card-custom p-4 my-4">
            <h4 class="fw-bold text-white mb-3">🔍 Обекти и разрешителни на живо</h4>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>Обект</th><th>Категория</th><th>Локация</th><th>Възложител</th><th>Параметри</th><th>Действие</th></tr>
                    </thead>
                    <tbody>
                        {% for p in projects %}
                        <tr>
                            <td class="fw-bold text-white">{{ p[1] }}</td>
                            <td><span class="badge bg-secondary">{{ p[2] }}</span></td>
                            <td>{{ p[3] }}</td>
                            <td class="text-info">{{ p[4] }}</td>
                            <td>{{ "€{:,.0f}".format(p[6]) if p[6] > 0 else p[5] }}</td>
                            <td>
                                <button class="btn btn-outline-primary btn-sm" onclick="openInquiryModal({{ p[0] }}, '{{ p[1] | replace("'", "") }}')">📩 Свържи ме</button>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </section>
    </main>

    <div class="modal fade" id="inquiryModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content bg-dark text-light border-secondary">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title">📩 Заявка за връзка с инвеститора</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form action="/api/submit-inquiry" method="POST">
                    <div class="modal-body">
                        <input type="hidden" id="modal_project_id" name="project_id">
                        <input type="hidden" id="modal_project_title" name="project_title">
                        <p class="small text-secondary mb-3">Обект: <strong id="display_project_title" class="text-info"></strong></p>
                        <div class="mb-2">
                            <input type="text" name="company" class="form-control bg-secondary text-light border-0" placeholder="Вашата фирма" required>
                        </div>
                        <div class="mb-2">
                            <input type="email" name="email" class="form-control bg-secondary text-light border-0" placeholder="Имейл адрес" required>
                        </div>
                        <div class="mb-2">
                            <input type="text" name="phone" class="form-control bg-secondary text-light border-0" placeholder="Телефон" required>
                        </div>
                        <div class="mb-2">
                            <select name="service_type" class="form-select bg-secondary text-light border-0">
                                <option value="Груб строеж / Изкопи / Бетон">Груб строеж / Изкопи / Бетон</option>
                                <option value="Електро / ОВК / ВиК инсталации">Електро / ОВК / ВиК инсталации</option>
                                <option value="Дограма, Фасади и Изолации">Дограма, Фасади и Изолации</option>
                                <option value="Доставка на строителни материали">Доставка на строителни материали</option>
                            </select>
                        </div>
                        <div class="mb-2">
                            <textarea name="message" class="form-control bg-secondary text-light border-0" rows="2" placeholder="Кратка бележка / опит..."></textarea>
                        </div>
                    </div>
                    <div class="modal-footer border-secondary">
                        <button type="submit" class="btn btn-primary">Изпрати заявката</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <footer class="border-top border-secondary py-4 mt-5 text-center text-secondary small">
        <div class="container d-flex flex-column flex-md-row justify-content-between align-items-center gap-2">
            <div>© 2026 Stroy Radar AI. Всички права запазени.</div>
            <div class="d-flex gap-3">
                <a href="mailto:kovko.firma@gmail.com" class="text-info text-decoration-none">✉️ kovko.firma@gmail.com</a>
                <a href="viber://chat" class="text-light text-decoration-none">💬 Viber Поддръжка</a>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
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

        function openInquiryModal(id, title) {
            document.getElementById('modal_project_id').value = id;
            document.getElementById('modal_project_title').value = title;
            document.getElementById('display_project_title').innerText = title;
            new bootstrap.Modal(document.getElementById('inquiryModal')).show();
        }
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
                <a href="/api/export-leads-csv" class="btn btn-success btn-sm">📥 Свали CSV</a>
                <a href="/logout" class="btn btn-outline-danger btn-sm">Изход</a>
            </div>
        </div>

        <div class="card card-custom p-4">
            <h4 class="fw-bold text-white mb-3">Обекти в реално време & Директна заявка</h4>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>Обект</th><th>Категория</th><th>Локация</th><th>Възложител</th><th>Параметри</th></tr>
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
                <h2 class="fw-bold text-warning">🤖 Напълно Автономно Управление</h2>
                <small class="text-secondary">Автоматичен бюлетин в 07:30 ч. | Автоматичен аутрийч в 08:00 ч.</small>
            </div>
            <a href="/" class="btn btn-outline-light btn-sm">← Към сайта</a>
        </div>

        <div class="card card-custom p-4 mb-4">
            <h4 class="fw-bold text-white mb-3">🔥 Класиране на лидовете по активност (Lead Scoring)</h4>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>Lead Score</th><th>Температура</th><th>Фирма</th><th>Имейл</th><th>Телефон</th><th>Статус</th></tr>
                    </thead>
                    <tbody>
                        {% for l in leads %}
                        <tr>
                            <td><span class="badge bg-primary fs-6">{{ l[5] }} т.</span></td>
                            <td>
                                {% if l[5] >= 50 %}
                                    <span class="badge bg-danger">🔥 Горещ (Hot)</span>
                                {% elif l[5] >= 20 %}
                                    <span class="badge bg-warning text-dark">🟡 Топъл (Warm)</span>
                                {% else %}
                                    <span class="badge bg-secondary">⚪ Студен (Cold)</span>
                                {% endif %}
                            </td>
                            <td class="fw-bold text-white">{{ l[2] }}</td>
                            <td><code>{{ l[1] }}</code></td>
                            <td>{{ l[3] if l[3] else '—' }}</td>
                            <td><span class="badge bg-info text-dark">{{ l[4] }}</span></td>
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, size_rzp, price_eur, status, lat, lng FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    return render_template_string(MAIN_HTML, projects=projects, projects_json=json.dumps(projects))

@app.route("/portal")
def portal():
    if "user_email" not in session:
        return redirect(url_for("login"))
    
    add_lead_score(session["user_email"], 10)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, size_rzp, price_eur, status FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    return render_template_string(PORTAL_HTML, user_email=session["user_email"], projects=projects)

@app.route("/admin")
def admin_panel():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, company_name, phone, status, score FROM leads_outreach ORDER BY score DESC, id DESC LIMIT 50")
    leads = c.fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, leads=leads)

@app.route("/api/submit-inquiry", methods=["POST"])
def submit_inquiry():
    project_id = request.form.get("project_id")
    project_title = request.form.get("project_title")
    company = request.form.get("company", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    service_type = request.form.get("service_type", "").strip()
    message = request.form.get("message", "").strip()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO project_inquiries (project_id, project_title, applicant_company, applicant_email, applicant_phone, service_type, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (project_id, project_title, company, email, phone, service_type, message))
    conn.commit()
    conn.close()

    add_lead_score(email, 50)

    send_email_msg(
        "kovko.firma@gmail.com",
        f"🔥 Горещ Лийд (+50 т.) Заявка за обект: {project_title}",
        f"<p>Фирма: {company}<br>Имейл: {email}<br>Тел: {phone}<br>Дейност: {service_type}</p>"
    )

    return "<script>alert('Заявката ви е приета успешно!'); window.location.href='/';</script>"

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
        return "<script>alert('Невалиден имейл домейн!'); window.history.back();</script>"

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO leads_outreach (email, company_name, phone, status, score, trial_start, sent_at) 
        VALUES (?, ?, ?, 'trial_active', 15, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(email) DO UPDATE SET company_name=excluded.company_name, phone=excluded.phone, status='trial_active'
    """, (email, company, phone))
    conn.commit()
    conn.close()

    session["user_email"] = email
    return redirect(url_for("portal"))

@app.route("/api/export-leads-csv")
def export_leads():
    if "user_email" in session:
        add_lead_score(session["user_email"], 25)

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
