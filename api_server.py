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

# --- 1. База данни с нови фирмени полета ---
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
            eik TEXT DEFAULT '205849120',
            manager TEXT DEFAULT 'Инж. Димитър Георгиев',
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

    try:
        c.execute("ALTER TABLE radar_projects ADD COLUMN eik TEXT DEFAULT '205849120'")
        c.execute("ALTER TABLE radar_projects ADD COLUMN manager TEXT DEFAULT 'Инж. Димитър Георгиев'")
    except Exception:
        pass

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

# --- 2. Zero-Bounce & SMTP модул ---
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

# --- 3. Автономен Двигател: Аутрийч + Drip Follow-Up (Ден 3 и 6) ---
def execute_outreach_and_followups():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Нови покани (20 фирми)
    c.execute("SELECT id, email, company_name FROM leads_outreach WHERE status = 'pending' LIMIT 20")
    pending_leads = c.fetchall()
    for lead_id, email, company in pending_leads:
        comp_name = company if company else "Колеги"
        subject = "Нови разрешителни за строеж и търгове за вашия район – Stroy Radar AI"
        body = f"""
        <div style='font-family:Segoe UI, sans-serif; background:#0f172a; color:#f8fafc; padding:25px; border-radius:10px; max-width:600px;'>
            <h2 style='color:#38bdf8; margin-top:0;'>🏗️ Stroy Radar AI</h2>
            <p>Здравейте, {comp_name},</p>
            <p>Платформата следи в реално време новоиздадените разрешения за строеж по ЗУТ и публичните търгове на ЧСИ в България.</p>
            <p>Предоставяме ви <strong>7-дневен безплатен пълен достъп</strong> с интерактивна GIS карта и данни за инвеститорите.</p>
            <p><a href='https://stroy-radar-ai.onrender.com' style='background:#2563eb; color:#ffffff; padding:12px 24px; text-decoration:none; border-radius:6px; font-weight:bold; display:inline-block;'>Вход в платформата</a></p>
        </div>
        """
        if send_email_msg(email, subject, body):
            c.execute("UPDATE leads_outreach SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?", (lead_id,))
            conn.commit()
            time.sleep(2)

    # 2. Drip Follow-Up: Ден 3
    c.execute("""
        SELECT id, email, company_name FROM leads_outreach 
        WHERE status = 'trial_active' AND last_followup_day = 0 
        AND julianday('now') - julianday(trial_start) >= 3
    """)
    day3_leads = c.fetchall()
    for lead_id, email, company in day3_leads:
        subj = "🏗️ Нови обекти за подизпълнение от днес – Stroy Radar AI"
        b_html = f"""
        <div style='font-family:Segoe UI, sans-serif; background:#0f172a; color:#f8fafc; padding:20px; border-radius:8px;'>
            <h3 style='color:#38bdf8;'>Здравейте, {company}!</h3>
            <p>През последните 48 часа са регистрирани нови строителни обекти с издадени разрешения за строеж.</p>
            <p>Прегледайте актуалните инвеститори и параметри в портала:</p>
            <p><a href='https://stroy-radar-ai.onrender.com/portal' style='background:#2563eb; color:#fff; padding:10px 20px; text-decoration:none; border-radius:6px; display:inline-block;'>Отвори Портала</a></p>
        </div>
        """
        send_email_msg(email, subj, b_html)
        c.execute("UPDATE leads_outreach SET last_followup_day = 3 WHERE id = ?", (lead_id,))
        conn.commit()

    # 3. Drip Follow-Up: Ден 6 (Напомняне преди изтичане)
    c.execute("""
        SELECT id, email, company_name FROM leads_outreach 
        WHERE status = 'trial_active' AND last_followup_day = 3 
        AND julianday('now') - julianday(trial_start) >= 6
    """)
    day6_leads = c.fetchall()
    for lead_id, email, company in day6_leads:
        subj = "⏳ Вашият 7-дневен тестов период в Stroy Radar AI изтича утре"
        b_html = f"""
        <div style='font-family:Segoe UI, sans-serif; background:#0f172a; color:#f8fafc; padding:20px; border-radius:8px;'>
            <h3 style='color:#f59e0b;'>Здравейте, {company},</h3>
            <p>Напомняме ви, че 7-дневният безплатен достъп до новите строителни обекти и търгове изтича след 24 часа.</p>
            <p>За въпроси, фактуриране или продължаване на абонамента, пишете ни на <a href='mailto:kovko.firma@gmail.com' style='color:#38bdf8;'>kovko.firma@gmail.com</a> или се свържете с нас във Viber.</p>
            <p><a href='https://stroy-radar-ai.onrender.com/portal' style='background:#10b981; color:#fff; padding:10px 20px; text-decoration:none; border-radius:6px; display:inline-block;'>Преглед на профила</a></p>
        </div>
        """
        send_email_msg(email, subj, b_html)
        c.execute("UPDATE leads_outreach SET last_followup_day = 6 WHERE id = ?", (lead_id,))
        conn.commit()

    conn.close()

# --- 4. 24/7 Scheduler ---
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

            # 07:30 ч. - Сутрешен Бюлетин
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
                send_email_msg("kovko.firma@gmail.com", f"🏗️ Сутрешен Строителен Радар ({now_bg.strftime('%d.%m.%Y')})", f"<div style='font-family:sans-serif; background:#0f172a; color:#fff; padding:20px;'>{items_html}</div>")
                already_sent_digest = True

            # 08:00 ч. - Автономен аутрийч + Drip кампании
            if time_str == "08:00" and not already_sent_outreach:
                execute_outreach_and_followups()
                already_sent_outreach = True

            time.sleep(30)
        except Exception:
            time.sleep(60)

threading.Thread(target=background_scheduler, daemon=True).start()

# --- 5. HTML Шаблони с Company Enrichment & PDF Print ---
MAIN_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stroy Radar AI – ConTech Платформа</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }
        .btn-brand { background: #2563eb; color: #fff; font-weight: 600; border-radius: 8px; }
        .btn-viber { background: #7360f2; color: #fff; font-weight: 600; border-radius: 8px; }
        #map { height: 380px; width: 100%; border-radius: 12px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold text-primary" href="/">🏗️ STROY RADAR AI</a>
            <div class="d-flex gap-2">
                <a href="/export-pdf" target="_blank" class="btn btn-outline-light btn-sm">📄 Експорт Доклад (PDF)</a>
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
                <p class="text-secondary lead fs-6">Пълни данни за инвеститори (ЕИК, Управител), сателитна карта и експорт на седмични доклади.</p>
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
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="fw-bold text-white mb-0">🔍 Обекти с фирмени данни (ЕИК & Управител)</h4>
                <a href="/export-pdf" target="_blank" class="btn btn-outline-success btn-sm">🖨️ Генерирай Седмичен Доклад</a>
            </div>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>Обект</th><th>Категория</th><th>Локация</th><th>Инвеститор / ЕИК</th><th>Управител</th><th>Параметри</th><th>Действие</th></tr>
                    </thead>
                    <tbody>
                        {% for p in projects %}
                        <tr>
                            <td class="fw-bold text-white">{{ p[1] }}</td>
                            <td><span class="badge bg-secondary">{{ p[2] }}</span></td>
                            <td>{{ p[3] }}</td>
                            <td><strong class="text-info">{{ p[4] }}</strong><br><small class="text-secondary">ЕИК: {{ p[5] }}</small></td>
                            <td><small class="text-light">{{ p[6] }}</small></td>
                            <td>{{ "€{:,.0f}".format(p[8]) if p[8] > 0 else p[7] }}</td>
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

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([42.6977, 24.5], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap' }).addTo(map);
        var projectsData = {{ projects_json | safe }};
        projectsData.forEach(function(item) {
            var lat = item[10] || 42.6977;
            var lng = item[11] || 23.3219;
            var priceOrSize = item[8] > 0 ? "€" + item[8].toLocaleString() : item[7];
            L.marker([lat, lng]).addTo(map).bindPopup("<strong>" + item[1] + "</strong><br>" + item[3] + "<br><b>Инвеститор:</b> " + item[4] + "<br>" + priceOrSize);
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

PDF_REPORT_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <title>Седмичен Строителен Доклад - Stroy Radar AI</title>
    <style>
        body { font-family: Arial, sans-serif; color: #1e293b; padding: 20px; line-height: 1.4; }
        .header { border-bottom: 2px solid #2563eb; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .title { color: #2563eb; font-size: 22px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; }
        th, td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; }
        th { background-color: #f1f5f9; }
        .badge { background: #e2e8f0; padding: 3px 6px; border-radius: 4px; font-weight: bold; }
        @media print { .no-print { display: none; } }
    </style>
</head>
<body>
    <div class="no-print" style="margin-bottom: 15px;">
        <button onclick="window.print()" style="background:#2563eb; color:#fff; border:none; padding:8px 16px; border-radius:6px; cursor:pointer; font-weight:bold;">🖨️ Разпечатай / Запази като PDF</button>
    </div>
    <div class="header">
        <div>
            <div class="title">🏗️ STROY RADAR AI – ОФИЦИАЛЕН СТРОИТЕЛЕН БЮЛЕТИН</div>
            <div>Седмичен доклад за нови строителни разрешителни и публични продажби в България</div>
        </div>
        <div><strong>Дата:</strong> {{ now_date }}</div>
    </div>
    <table>
        <thead>
            <tr>
                <th>Обект</th>
                <th>Категория</th>
                <th>Локация</th>
                <th>Възложител / Инвеститор</th>
                <th>ЕИК</th>
                <th>Управител</th>
                <th>Параметри / Цена</th>
            </tr>
        </thead>
        <tbody>
            {% for p in projects %}
            <tr>
                <td><strong>{{ p[1] }}</strong></td>
                <td><span class="badge">{{ p[2] }}</span></td>
                <td>{{ p[3] }}</td>
                <td>{{ p[4] }}</td>
                <td>{{ p[5] }}</td>
                <td>{{ p[6] }}</td>
                <td>{{ "€{:,.0f}".format(p[8]) if p[8] > 0 else p[7] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <div style="margin-top: 30px; font-size: 11px; color: #64748b; border-top: 1px solid #cbd5e1; padding-top: 10px;">
        Генерирано от Stroy Radar AI ConTech Platform | За контакт и фактуриране: kovko.firma@gmail.com
    </div>
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
                <a href="/export-pdf" target="_blank" class="btn btn-outline-light btn-sm">📄 Свали PDF Доклад</a>
                <a href="/api/export-leads-csv" class="btn btn-success btn-sm">📥 Свали CSV</a>
                <a href="/logout" class="btn btn-outline-danger btn-sm">Изход</a>
            </div>
        </div>

        <div class="card card-custom p-4">
            <h4 class="fw-bold text-white mb-3">Обекти в реално време & Фирмени профили</h4>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>Обект</th><th>Категория</th><th>Локация</th><th>Инвеститор</th><th>ЕИК</th><th>Управител</th><th>Параметри</th></tr>
                    </thead>
                    <tbody>
                        {% for p in projects %}
                        <tr>
                            <td class="fw-bold text-white">{{ p[1] }}</td>
                            <td><span class="badge bg-secondary">{{ p[2] }}</span></td>
                            <td>{{ p[3] }}</td>
                            <td class="text-info">{{ p[4] }}</td>
                            <td><code>{{ p[5] }}</code></td>
                            <td>{{ p[6] }}</td>
                            <td>{{ "€{:,.0f}".format(p[8]) if p[8] > 0 else p[7] }}</td>
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
                <h2 class="fw-bold text-warning">🤖 Напълно Автономно Управление + Drip Фуния</h2>
                <small class="text-secondary">Бюлетин (07:30 ч.) | Аутрийч (08:00 ч.) | Drip Follow-ups (Ден 3 и Ден 6)</small>
            </div>
            <a href="/" class="btn btn-outline-light btn-sm">← Към сайта</a>
        </div>

        <div class="card card-custom p-4 mb-4">
            <h4 class="fw-bold text-white mb-3">🔥 Класиране на лидовете по активност (Lead Scoring)</h4>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small"><th>Lead Score</th><th>Температура</th><th>Фирма</th><th>Имейл</th><th>Телефон</th><th>Follow-Up Етап</th><th>Статус</th></tr>
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
                            <td><span class="badge bg-secondary">Ден {{ l[6] }}</span></td>
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
    c.execute("SELECT id, title, category, location, investor, eik, manager, size_rzp, price_eur, status, lat, lng FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    return render_template_string(MAIN_HTML, projects=projects, projects_json=json.dumps(projects))

@app.route("/export-pdf")
def export_pdf_report():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, eik, manager, size_rzp, price_eur FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    now_str = datetime.now(ZoneInfo("Europe/Sofia")).strftime("%d.%m.%Y")
    return render_template_string(PDF_REPORT_HTML, projects=projects, now_date=now_str)

@app.route("/portal")
def portal():
    if "user_email" not in session:
        return redirect(url_for("login"))
    
    add_lead_score(session["user_email"], 10)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, eik, manager, size_rzp, price_eur, status FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    return render_template_string(PORTAL_HTML, user_email=session["user_email"], projects=projects)

@app.route("/admin")
def admin_panel():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, company_name, phone, status, score, last_followup_day FROM leads_outreach ORDER BY score DESC, id DESC LIMIT 50")
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
    c.execute("SELECT id, title, category, location, investor, eik, manager, size_rzp, price_eur FROM radar_projects ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["ID", "Обект", "Категория", "Локация", "Инвеститор", "ЕИК", "Управител", "РЗП/Площ", "Цена (€)"])
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
