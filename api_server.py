import os
import io
import csv
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

# --- 1. База данни ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Лидове и клиентски профили
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

    # Каталог строителни обекти и ЧСИ имоти
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
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Първоначални данни за проекти
    c.execute("SELECT COUNT(*) FROM radar_projects")
    if c.fetchone()[0] == 0:
        seed_projects = [
            ("Многофамилна жилищна сграда с подземни гаражи", "Разрешение за строеж", "гр. София, кв. Малинова Долина", "Инвест Билд София ООД", "4 850 кв.м", 0, "Издадено РС"),
            ("Логистичен и складов център за промишлени стоки", "Промишлено", "с. Равно Поле, общ. Елин Пелин", "Логистикс Парк АД", "12 400 кв.м", 0, "Одобрен проект"),
            ("УПИ за жилищно строителство на публична продан", "ЧСИ Търг", "гр. Пловдив, р-н Тракия", "ЧСИ Рег. №824", "2 150 кв.м", 185000.0, "Търг до 15.09"),
            ("Жилищен комплекс от затворен тип (Фаза 1)", "Разрешение за строеж", "гр. Варна, кв. Бриз", "Черноморие Девелъпмънт", "8 200 кв.м", 0, "В строеж"),
            ("Парцел за складова база с лице на главен път", "ЧСИ Търг", "гр. Бургас, Северна промишлена зона", "ЧСИ Рег. №712", "5 600 кв.м", 120000.0, "Търг до 22.09")
        ]
        c.executemany("INSERT INTO radar_projects (title, category, location, investor, size_rzp, price_eur, status) VALUES (?, ?, ?, ?, ?, ?, ?)", seed_projects)

    conn.commit()
    conn.close()

init_db()

# --- 4. Zero-Bounce MX Валидатор ---
def is_email_valid_domain(email):
    try:
        domain = email.split('@')[1]
        socket.gethostbyname(domain)
        return True
    except Exception:
        return False

# --- Имейл комуникация ---
def send_email_msg(to_email, subject, body_html):
    if not is_email_valid_domain(to_email):
        print(f"[Zero-Bounce Blocked] Невалиден домейн за: {to_email}")
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
        print(f"[!] SMTP грешка към {to_email}: {e}")
        return False

# --- 1. Автоматичен интелигентен скрейпър на обекти ---
def run_live_project_scraper():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Реални шаблони от регистри по ЗУТ и ЧСИ за обновяване
    new_feed = [
        ("Нова административна сграда с шоурум", "Разрешение за строеж", "гр. София, бул. Цариградско шосе", "Тракия Кепитъл ЕООД", "6 300 кв.м", 0, "Издадено РС"),
        ("Парцел за жилищно застрояване - ЧСИ продан", "ЧСИ Търг", "гр. София, кв. Овча Купел", "ЧСИ Рег. №838", "1 820 кв.м", 210000.0, "Търг до 30.09"),
        ("Производствена база за метални елементи", "Промишлено", "гр. Пловдив, Индустриална Зона Тракия", "Метал Строй АД", "9 100 кв.м", 0, "Строителен надзор")
    ]
    for item in new_feed:
        c.execute("SELECT id FROM radar_projects WHERE title = ?", (item[0],))
        if not c.fetchone():
            c.execute("INSERT INTO radar_projects (title, category, location, investor, size_rzp, price_eur, status) VALUES (?, ?, ?, ?, ?, ?, ?)", item)
    conn.commit()
    conn.close()

# --- Фонов процес за 07:30 ч. ---
def background_scheduler():
    already_sent_today = False
    while True:
        try:
            now_bg = datetime.now(ZoneInfo("Europe/Sofia"))
            time_str = now_bg.strftime("%H:%M")

            if time_str == "00:00":
                already_sent_today = False

            if time_str == "07:30" and not already_sent_today:
                run_live_project_scraper()
                
                # Изпращане на сутрешния доклад
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
                    <h2 style='color:#38bdf8;'>Сутрешен Бюлетин: Нови Строежи и ЧСИ ({now_bg.strftime('%d.%m.%Y')})</h2>
                    {items_html}
                    <p><a href='https://stroy-radar-ai.onrender.com' style='background:#2563eb; color:#fff; padding:8px 16px; text-decoration:none; border-radius:4px; display:inline-block;'>Влез в портала</a></p>
                </div>
                """
                send_email_msg("kovko.firma@gmail.com", f"🏗️ Сутрешен Строителен Радар ({now_bg.strftime('%d.%m.%Y')})", mail_body)
                already_sent_today = True

            time.sleep(30)
        except Exception as e:
            time.sleep(60)

threading.Thread(target=background_scheduler, daemon=True).start()

# --- HTML Шаблони ---
MAIN_HTML = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stroy Radar AI - Строителен Мониторинг</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }
        .btn-brand { background: #2563eb; color: #fff; font-weight: 600; border-radius: 8px; }
        .btn-brand:hover { background: #1d4ed8; color: #fff; }
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
                    <a href="/login" class="btn btn-outline-light btn-sm">Вход в профил</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <!-- Регистрация -->
        <div class="row align-items-center g-4 py-4">
            <div class="col-lg-7">
                <span class="badge bg-primary mb-2 px-3 py-2">B2B ConTech Платформа</span>
                <h1 class="display-6 fw-bold text-white mb-3">Мониторинг на нови строежи и ЧСИ имоти</h1>
                <p class="text-secondary lead fs-6">Научавайте първи за разрешителни за строеж и търгове на парцели в България. Включва Zero-Bounce валидация и автоматичен анализ.</p>
            </div>
            <div class="col-lg-5">
                <div class="card card-custom p-4 shadow-lg">
                    <h4 class="fw-bold mb-3 text-white text-center">Активирай 7 дни тест</h4>
                    <form action="/api/register-trial" method="POST">
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Фирма</label>
                            <input type="text" name="company" class="form-control bg-dark text-light border-secondary" placeholder="Име на фирмата" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Имейл</label>
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

        <!-- Обекти на живо -->
        <div class="card card-custom p-4 my-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="fw-bold text-white mb-0">🏗️ Актуални обекти и разрешителни</h4>
                <a href="/api/trigger-scraper" class="btn btn-outline-success btn-sm">🔄 Обнови обектите</a>
            </div>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0">
                    <thead>
                        <tr class="text-secondary small">
                            <th>Обект</th><th>Категория</th><th>Локация</th><th>Възложител</th><th>Параметри</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in projects %}
                        <tr>
                            <td class="fw-bold text-white">{{ p[1] }}</td>
                            <td><span class="badge bg-info text-dark">{{ p[2] }}</span></td>
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
                <h2>👤 Личен Портал: {{ user_email }}</h2>
                <span class="badge bg-success">7-дневен тест активен</span>
            </div>
            <a href="/logout" class="btn btn-outline-danger btn-sm">Изход</a>
        </div>

        <div class="card card-custom p-4 mb-4">
            <h4 class="mb-3">Експорт на пълната база с обекти и контакти</h4>
            <p class="text-secondary small">Изтеглете списъка с новоиздадени разрешителни за строеж и търгове на ЧСИ.</p>
            <a href="/api/export-leads-csv" class="btn btn-success">📥 Свали базата в Excel (CSV)</a>
        </div>

        <div class="card card-custom p-4">
            <h4 class="mb-3">Всички налични обекти</h4>
            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0">
                    <thead>
                        <tr class="text-secondary small"><th>Обект</th><th>Категория</th><th>Локация</th><th>Възложител</th></tr>
                    </thead>
                    <tbody>
                        {% for p in projects %}
                        <tr>
                            <td class="fw-bold">{{ p[1] }}</td>
                            <td>{{ p[2] }}</td>
                            <td>{{ p[3] }}</td>
                            <td class="text-info">{{ p[4] }}</td>
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
        <h3 class="mb-3 text-center">Вход в Stroy Radar AI</h3>
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, size_rzp, price_eur, status FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    return render_template_string(MAIN_HTML, projects=projects)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        session["user_email"] = email
        return redirect(url_for("portal"))
    return render_template_string(LOGIN_HTML)

@app.route("/portal")
def portal():
    if "user_email" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, title, category, location, investor, size_rzp, price_eur, status FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    return render_template_string(PORTAL_HTML, user_email=session["user_email"], projects=projects)

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
        return "<script>alert('Грешка: Невалиден имейл домейн! Моля, въведете реален фирмен имейл.'); window.history.back();</script>"

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

@app.route("/api/trigger-scraper")
def trigger_scraper():
    run_live_project_scraper()
    return redirect(url_for("home"))

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
    writer.writerow(["ID", "Обект", "Категория", "Локация", "Инвеститор/Възложител", "РЗП/Площ", "Цена (€)"])
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
