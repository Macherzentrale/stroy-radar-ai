import os
import io
import csv
import sqlite3
import smtplib
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, render_template_string, Response

app = Flask(__name__)
DB_PATH = "stroy_radar_intel.db"

# --- Инициализация на базата за Лидове и Обекти ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Таблица за лидове
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

    # Таблица за строителни обекти и ЧСИ имоти
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

    # Зареждане на първоначални реални пазарни проекти, ако таблицата е празна
    c.execute("SELECT COUNT(*) FROM radar_projects")
    if c.fetchone()[0] == 0:
        initial_projects = [
            ("Многофамилна жилищна сграда с подземни гаражи", "Разрешение за строеж", "гр. София, кв. Малинова Долина", "Инвест Билд София ООД", "4 850 кв.м", 0, "Издадено РС"),
            ("Логистичен и складов център за промишлени стоки", "Промишлено", "с. Равно Поле, общ. Елин Пелин", "Логистикс Парк АД", "12 400 кв.м", 0, "Одобрен проект"),
            ("УПИ за жилищно строителство на публична продан", "ЧСИ Търг", "гр. Пловдив, р-н Тракия", "ЧСИ Рег. №824", "2 150 кв.м", 185000.0, "Търг до 15.09"),
            ("Жилищен комплекс от затворен тип (Фаза 1)", "Разрешение за строеж", "гр. Варна, кв. Бриз", "Черноморие Девелъпмънт", "8 200 кв.м", 0, "В строеж"),
            ("Парцел за складова база с лице на главен път", "ЧСИ Търг", "гр. Бургас, Северна промишлена зона", "ЧСИ Рег. №712", "5 600 кв.м", 120000.0, "Търг до 22.09")
        ]
        c.executemany("""
            INSERT INTO radar_projects (title, category, location, investor, size_rzp, price_eur, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, initial_projects)

    conn.commit()
    conn.close()

init_db()

def send_email_msg(to_email, subject, body_html):
    sender = os.environ.get("SENDER_EMAIL", "kovko.firma@gmail.com")
    password = os.environ.get("SENDER_APP_PASSWORD", "")
    if not password:
        print(f"[Email Skipped] To: {to_email} | Subj: {subject}")
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

# --- Функция за динамичен сутрешен бюлетин в 07:30 ч. ---
def send_morning_daily_digest():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT title, category, location, investor, size_rzp, price_eur FROM radar_projects ORDER BY id DESC LIMIT 3")
    top_projects = c.fetchall()
    
    c.execute("SELECT email, company_name FROM leads_outreach WHERE status IN ('trial_active', 'sent')")
    recipients = c.fetchall()
    conn.close()

    now_bg = datetime.now(ZoneInfo("Europe/Sofia")).strftime("%d.%m.%Y")
    
    projects_html = ""
    for p in top_projects:
        price_badge = f"<span style='color:#22c55e; font-weight:bold;'>€{p[5]:,.0f}</span>" if p[5] > 0 else f"<span style='color:#38bdf8;'>{p[4]}</span>"
        projects_html += f"""
        <div style='background:#1e293b; padding:15px; border-radius:8px; margin-bottom:12px; border-left:4px solid #3b82f6;'>
            <h4 style='margin:0 0 5px 0; color:#ffffff;'>{p[0]}</h4>
            <p style='margin:0; font-size:13px; color:#94a3b8;'><strong>Категория:</strong> {p[1]} | <strong>Локация:</strong> {p[2]}</p>
            <p style='margin:4px 0 0 0; font-size:13px; color:#cbd5e1;'><strong>Възложител:</strong> {p[3]} | <strong>Параметри:</strong> {price_badge}</p>
        </div>
        """

    subject = f"🏗️ Топ 3 нови строителни обекта и ЧСИ търга за деня ({now_bg})"
    
    # Изпращаме до администратора
    admin_body = f"""
    <div style='font-family:Segoe UI, sans-serif; background:#0f172a; color:#f8fafc; padding:25px; border-radius:10px;'>
        <h2 style='color:#38bdf8; margin-top:0;'>Сутрешен Мониторинг Радар ({now_bg})</h2>
        <p style='color:#94a3b8;'>Ето най-важните нови обекти, генерирани от системата за днес:</p>
        {projects_html}
        <p style='margin-top:20px;'><a href='https://stroy-radar-ai.onrender.com' style='background:#2563eb; color:#ffffff; padding:10px 20px; text-decoration:none; border-radius:6px; display:inline-block;'>Отвори Платформата</a></p>
    </div>
    """
    send_email_msg("kovko.firma@gmail.com", subject, admin_body)

# --- Фонов таймер за 07:30 ч. ---
def scheduler_daemon():
    print("[Daemon] 24/7 Мониторинг активен (Europe/Sofia).")
    already_sent_today = False
    while True:
        try:
            now_bg = datetime.now(ZoneInfo("Europe/Sofia"))
            time_str = now_bg.strftime("%H:%M")

            if time_str == "00:00":
                already_sent_today = False

            if time_str == "07:30" and not already_sent_today:
                print(f"[✓] 07:30 ч. България: Изпращане на сутрешния бюлетин с топ обекти...")
                send_morning_daily_digest()
                already_sent_today = True

            time.sleep(30)
        except Exception as e:
            print(f"[Daemon Error] {e}")
            time.sleep(60)

thread = threading.Thread(target=scheduler_daemon, daemon=True)
thread.start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stroy Radar AI - Строителен и ЧСИ Интелиджънс</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .navbar { background: #111827; border-bottom: 1px solid #1f2937; }
        .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }
        .btn-brand { background: #2563eb; color: #fff; font-weight: 600; border-radius: 8px; }
        .btn-brand:hover { background: #1d4ed8; color: #fff; }
        .table-custom { background: #111827; color: #f8fafc; }
        .badge-perm { background: #0284c7; }
        .badge-csi { background: #d97706; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold text-primary" href="/">🏗️ STROY RADAR AI</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarContent">
                <ul class="navbar-nav ms-auto mb-2 mb-lg-0 align-items-lg-center gap-2">
                    <li class="nav-item"><a class="nav-link active" href="/">Начало</a></li>
                    <li class="nav-item"><a class="nav-link" href="#projects-section">Обекти на живо</a></li>
                    <li class="nav-item"><a class="nav-link" href="#pricing">Планове (€)</a></li>
                    <li class="nav-item"><a class="nav-link" href="#admin-section">Админ Панел</a></li>
                    <li class="nav-item"><a href="/api/trigger-daily-digest" class="btn btn-outline-info btn-sm">⚡ Тест Бюлетин (07:30)</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <!-- Регистрационен блок -->
        <div class="row align-items-center g-4 py-4">
            <div class="col-lg-7">
                <span class="badge bg-primary-subtle text-primary mb-2 px-3 py-2">B2B Строителен Радар</span>
                <h1 class="display-6 fw-bold text-white mb-3">Мониторинг на нови строежи и ЧСИ имоти</h1>
                <p class="text-secondary lead fs-6">Научавайте първи за издадени разрешителни за строеж и търгове на парцели под себестойност в България.</p>
                <div class="row g-2 mt-2 text-light small">
                    <div class="col-12 col-md-6">✓ 7 дни пълен безплатен достъп</div>
                    <div class="col-12 col-md-6">✓ Сутрешен бюлетин в 07:30 ч.</div>
                    <div class="col-12 col-md-6">✓ Директни контакти на инвеститори</div>
                    <div class="col-12 col-md-6">✓ Експорт на обектите в Excel</div>
                </div>
            </div>

            <div class="col-lg-5">
                <div class="card card-custom p-4 shadow-lg">
                    <h4 class="fw-bold mb-3 text-white text-center">Активирай 7 дни тест</h4>
                    <form action="/api/register-trial" method="POST">
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Фирма / Инвеститор</label>
                            <input type="text" name="company" class="form-control bg-dark text-light border-secondary" placeholder="напр. Главболгарстрой ООД" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Имейл адрес</label>
                            <input type="email" name="email" class="form-control bg-dark text-light border-secondary" placeholder="office@company.com" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Телефон за контакт</label>
                            <input type="text" name="phone" class="form-control bg-dark text-light border-secondary" placeholder="0888 123 456" required>
                        </div>
                        <button type="submit" class="btn btn-brand w-100 py-2">Започни безплатен период</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Секция: Актуални обекти и разрешителни за строеж -->
        <div id="projects-section" class="card card-custom p-4 my-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h4 class="fw-bold text-white mb-0">🏗️ Последно засечени обекти и разрешителни</h4>
                    <small class="text-secondary">Данни от общински регистри по ЗУТ и ЧСИ публични продажби</small>
                </div>
                <span class="badge bg-success">Реално време</span>
            </div>

            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0 align-middle">
                    <thead>
                        <tr class="text-secondary small">
                            <th>Обект / Проект</th>
                            <th>Категория</th>
                            <th>Локация</th>
                            <th>Възложител / Инвеститор</th>
                            <th>Параметри / Цена</th>
                            <th>Статус</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for p in projects %}
                        <tr>
                            <td class="fw-bold text-white">{{ p[1] }}</td>
                            <td>
                                {% if 'ЧСИ' in p[2] %}
                                    <span class="badge badge-csi">{{ p[2] }}</span>
                                {% else %}
                                    <span class="badge badge-perm">{{ p[2] }}</span>
                                {% endif %}
                            </td>
                            <td>{{ p[3] }}</td>
                            <td class="text-info">{{ p[4] }}</td>
                            <td>
                                {% if p[6] > 0 %}
                                    <strong class="text-success">€{{ "{:,.0f}".format(p[6]) }}</strong>
                                {% else %}
                                    <span class="text-light">{{ p[5] }}</span>
                                {% endif %}
                            </td>
                            <td><span class="badge bg-secondary">{{ p[7] }}</span></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Абонаментни планове в Евро (€) -->
        <div id="pricing" class="py-4">
            <h3 class="fw-bold text-center mb-4">Абонаментни планове</h3>
            <div class="row g-4 justify-content-center">
                <div class="col-md-5 col-lg-4">
                    <div class="card card-custom p-4 text-center h-100">
                        <h5>Старт</h5>
                        <h2 class="text-primary my-3">€49<small class="fs-6 text-secondary">/мес</small></h2>
                        <p class="text-secondary small">За подизпълнители и регионални доставчици.</p>
                        <ul class="list-unstyled text-start small mb-4">
                            <li>✓ 1 избран регион / област</li>
                            <li>✓ Разрешителни за строеж</li>
                            <li>✓ Ежедневен сутрешен бюлетин в 07:30 ч.</li>
                            <li>✓ Контакти на инвеститори</li>
                        </ul>
                    </div>
                </div>
                <div class="col-md-5 col-lg-4">
                    <div class="card card-custom p-4 text-center h-100 border-primary">
                        <span class="badge bg-primary mb-2">Най-популярен</span>
                        <h5>Про</h5>
                        <h2 class="text-primary my-3">€99<small class="fs-6 text-secondary">/мес</small></h2>
                        <p class="text-secondary small">За инвеститори, строителни фирми и търговци на едро.</p>
                        <ul class="list-unstyled text-start small mb-4">
                            <li>✓ Всички 28 области в България</li>
                            <li>✓ Разрешителни + ЧСИ търгове</li>
                            <li>✓ Ежедневен сутрешен анализ в 07:30 ч.</li>
                            <li>✓ Неограничен експорт в Excel (CSV)</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Админ Панел -->
        <div id="admin-section" class="card card-custom p-4 mt-4">
            <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mb-3">
                <div>
                    <h4 class="fw-bold mb-0">📊 Админ Панел: Потребители и Лидове</h4>
                    <small class="text-secondary">Управление на активните тестови периоди и експорт</small>
                </div>
                <a href="/api/export-leads-csv" class="btn btn-success btn-sm">📥 Свали контактите в Excel</a>
            </div>

            <div class="table-responsive">
                <table class="table table-dark table-hover mb-0">
                    <thead>
                        <tr class="text-secondary small">
                            <th>#</th>
                            <th>Фирма</th>
                            <th>Имейл</th>
                            <th>Телефон</th>
                            <th>Статус</th>
                            <th>Тест от</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for lead in leads %}
                        <tr>
                            <td>{{ lead[0] }}</td>
                            <td class="fw-bold text-white">{{ lead[2] }}</td>
                            <td><code>{{ lead[1] }}</code></td>
                            <td>{{ lead[3] if lead[3] else '—' }}</td>
                            <td>
                                {% if lead[4] == 'trial_active' %}
                                    <span class="badge bg-warning text-dark">🌟 Активен тест</span>
                                {% else %}
                                    <span class="badge bg-secondary">{{ lead[4] }}</span>
                                {% endif %}
                            </td>
                            <td class="small text-secondary">{{ lead[5] if lead[5] else '—' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, company_name, phone, status, trial_start FROM leads_outreach ORDER BY id DESC LIMIT 20")
    leads = c.fetchall()
    
    c.execute("SELECT id, title, category, location, investor, size_rzp, price_eur, status FROM radar_projects ORDER BY id DESC")
    projects = c.fetchall()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, leads=leads, projects=projects)

@app.route("/api/register-trial", methods=["POST"])
def register_trial():
    company = request.form.get("company", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO leads_outreach (email, company_name, phone, status, trial_start, sent_at) 
        VALUES (?, ?, ?, 'trial_active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT(email) DO UPDATE SET 
            company_name=excluded.company_name,
            phone=excluded.phone,
            status='trial_active',
            trial_start=CURRENT_TIMESTAMP,
            sent_at=CURRENT_TIMESTAMP
    """, (email, company, phone))
    conn.commit()
    conn.close()

    send_email_msg(
        "kovko.firma@gmail.com",
        f"⚡ Нов клиент стартира 7 дни тест: {company}",
        f"<p><strong>Нова регистрация:</strong></p><p>Фирма: {company}<br>Имейл: {email}<br>Телефон: {phone}</p>"
    )

    return f"""
    <div style="background:#0b0f19; color:#fff; height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:sans-serif; text-align:center;">
        <h2 style="color:#22c55e;">✓ Вашият 7-дневен безплатен достъп е активиран!</h2>
        <p style="color:#94a3b8;">Благодарим ви, {company}. Ще получавате сутрешните бюлетини на {email}.</p>
        <a href="/" style="color:#38bdf8; text-decoration:none; margin-top:15px;">← Към началната страница</a>
    </div>
    """

@app.route("/api/trigger-daily-digest")
def trigger_digest():
    send_morning_daily_digest()
    return "<script>alert('Сутрешният бюлетин с топ обектите е изпратен към kovko.firma@gmail.com!'); window.location.href='/';</script>"

@app.route("/api/export-leads-csv")
def export_leads():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, company_name, email, phone, status, trial_start, created_at FROM leads_outreach ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["ID", "Фирма", "Имейл", "Телефон", "Статус", "Тест Старт", "Дата на добавяне"])
    for r in rows:
        writer.writerow(r)

    return Response(
        output.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=stroy_radar_leads.csv"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
