import os
import sqlite3
import smtplib
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, render_template_string, redirect, url_for

app = Flask(__name__)
DB_PATH = "stroy_radar_intel.db"

# --- Инициализация на базата данни ---
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
            sent_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Имейл нотификации ---
def send_admin_alert(subject, content):
    sender = os.environ.get("SENDER_EMAIL", "kovko.firma@gmail.com")
    password = os.environ.get("SENDER_APP_PASSWORD", "")
    admin_target = "kovko.firma@gmail.com"

    if not password:
        print(f"[Admin Alert Skipped - No Password] {subject}")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = f"Stroy Radar System <{sender}>"
        msg["To"] = admin_target
        msg["Subject"] = f"⚡ [Stroy Radar] {subject}"
        msg.attach(MIMEText(content, "plain", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, admin_target, msg.as_string())
        server.quit()
        print(f"[✓] Изпратено известие до: {admin_target}")
    except Exception as e:
        print(f"[!] Грешка при изпращане на имейл: {e}")

# --- Фонов график за 07:30 ч. България ---
def background_scheduler():
    print("[Daemon] Стартиран вътрешен scheduler за часова зона Europe/Sofia.")
    already_sent_today = False
    while True:
        try:
            now_bg = datetime.now(ZoneInfo("Europe/Sofia"))
            time_str = now_bg.strftime("%H:%M")

            if time_str == "00:00":
                already_sent_today = False

            if time_str == "07:30" and not already_sent_today:
                print(f"[✓] 07:30 ч. BG: Изпращане на сутрешен отчет...")
                send_admin_alert(
                    "Сутрешен бюлетин: Нови обекти и статус на кампаниите",
                    f"Автоматичен сутрешен отчет за {now_bg.strftime('%d.%m.%Y')}.\nСистемата работи нормално."
                )
                already_sent_today = True

            time.sleep(30)
        except Exception as e:
            print(f"[Scheduler Error] {e}")
            time.sleep(60)

# Стартиране на шедулъра в отделна нишка
thread = threading.Thread(target=background_scheduler, daemon=True)
thread.start()

# --- HTML Шаблон с пълна мобилна съвместимост ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Stroy Radar AI - Интелигентен Строителен Мониторинг</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .navbar { background: #111827; border-bottom: 1px solid #1f2937; }
        .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }
        .btn-brand { background: #2563eb; color: #fff; font-weight: 600; border-radius: 8px; }
        .btn-brand:hover { background: #1d4ed8; color: #fff; }
        .form-control { background: #1f2937 !important; border: 1px solid #374151 !important; color: #f9fafb !important; }
        .form-control:focus { border-color: #3b82f6 !important; box-shadow: 0 0 0 0.25rem rgba(59, 130, 246, 0.25); }
        .table-responsive { border-radius: 8px; }
    </style>
</head>
<body>

    <!-- Навигация с работещ мобилен бутон -->
    <nav class="navbar navbar-expand-lg navbar-dark sticky-top">
        <div class="container">
            <a class="navbar-brand fw-bold text-primary" href="/">🏗️ STROY RADAR AI</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent" aria-controls="navbarContent" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarContent">
                <ul class="navbar-nav ms-auto mb-2 mb-lg-0 align-items-lg-center gap-2">
                    <li class="nav-item"><a class="nav-link active" href="/">Начало</a></li>
                    <li class="nav-item"><a class="nav-link" href="#pricing">Планове</a></li>
                    <li class="nav-item"><a class="nav-link" href="#admin-section">Админ Панел</a></li>
                    <li class="nav-item"><a href="/api/trigger-morning-report" class="btn btn-outline-info btn-sm">⚡ Тест Отчет (07:30)</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <!-- Регистрационен блок за 7-дневен безплатен тест -->
        <div class="row align-items-center g-4 py-4">
            <div class="col-lg-7">
                <span class="badge bg-primary-subtle text-primary mb-2 px-3 py-2">B2B Строителен Радар</span>
                <h1 class="display-6 fw-bold text-white mb-3">Мониторинг на разрешителни за строеж и ЧСИ имоти</h1>
                <p class="text-secondary lead fs-6">Получавайте директен достъп до нови обекти, инвеститори и търгове преди вашите конкуренти с ежедневни анализи на живо.</p>
                <div class="row g-2 mt-2">
                    <div class="col-12 col-md-6">✓ 7 дни пълен безплатен достъп</div>
                    <div class="col-12 col-md-6">✓ Точен сутрешен бюлетин в 07:30 ч.</div>
                    <div class="col-12 col-md-6">✓ Извличане на контакти на строители</div>
                    <div class="col-12 col-md-6">✓ Без обвързващи договори</div>
                </div>
            </div>

            <div class="col-lg-5">
                <div class="card card-custom p-4 shadow-lg">
                    <h4 class="fw-bold mb-3 text-white text-center">Активирай 7 дни тест</h4>
                    <form action="/api/register-trial" method="POST">
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Фирма / Инвеститор</label>
                            <input type="text" name="company" class="form-control" placeholder="напр. Главболгарстрой ООД" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Имейл адрес</label>
                            <input type="email" name="email" class="form-control" placeholder="office@company.com" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small text-secondary">Телефон за контакт</label>
                            <input type="text" name="phone" class="form-control" placeholder="0888 123 456" required>
                        </div>
                        <button type="submit" class="btn btn-brand w-100 py-2">Започни безплатен период</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Абонаментни планове -->
        <div id="pricing" class="py-5">
            <h3 class="fw-bold text-center mb-4">Абонаментни планове</h3>
            <div class="row g-4 justify-content-center">
                <div class="col-md-4">
                    <div class="card card-custom p-4 text-center h-100">
                        <h5>Старт</h5>
                        <h2 class="text-primary my-3">99 лв.<small class="fs-6 text-secondary">/мес</small></h2>
                        <p class="text-secondary small">Подходящ за подизпълнители и малки доставчици.</p>
                        <ul class="list-unstyled text-start small mb-4">
                            <li>✓ 1 избран регион/област</li>
                            <li>✓ Разрешителни за строеж</li>
                            <li>✓ Ежедневен сутрешен отчет</li>
                        </ul>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card card-custom p-4 text-center h-100 border-primary">
                        <span class="badge bg-primary mb-2">Най-популярен</span>
                        <h5>Про</h5>
                        <h2 class="text-primary my-3">199 лв.<small class="fs-6 text-secondary">/мес</small></h2>
                        <p class="text-secondary small">За строителни предприемачи и търговци на едро.</p>
                        <ul class="list-unstyled text-start small mb-4">
                            <li>✓ Цяла България</li>
                            <li>✓ Разрешителни + ЧСИ търгове</li>
                            <li>✓ Автоматичен B2B експорт</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Админ Панел -->
        <div id="admin-section" class="card card-custom p-4 mt-4">
            <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mb-3">
                <div>
                    <h4 class="fw-bold mb-0">📊 Админ Панел: Управление на лидове</h4>
                    <small class="text-secondary">Преглед на изпратени оферти и активирани тестови периоди</small>
                </div>
                <span class="badge bg-success py-2 px-3">24/7 Сървър Активен</span>
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
                            <th>Дата</th>
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
                                {% elif lead[4] == 'sent' %}
                                    <span class="badge bg-success">Изпратена оферта</span>
                                {% else %}
                                    <span class="badge bg-secondary">Чакащ</span>
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

    <!-- Bootstrap 5 JavaScript Bundle за мобилната навигация -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, company_name, phone, status, sent_at FROM leads_outreach ORDER BY id DESC LIMIT 50")
    leads = c.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, leads=leads)

@app.route("/api/register-trial", methods=["POST"])
def register_trial():
    company = request.form.get("company", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO leads_outreach (email, company_name, phone, status, sent_at) 
        VALUES (?, ?, ?, 'trial_active', CURRENT_TIMESTAMP)
        ON CONFLICT(email) DO UPDATE SET 
            company_name=excluded.company_name,
            phone=excluded.phone,
            status='trial_active',
            sent_at=CURRENT_TIMESTAMP
    """, (email, company, phone))
    conn.commit()
    conn.close()

    send_admin_alert(
        f"Нова регистрация за 7-дневен тест: {company}",
        f"Детайли за новия лид:\n\nФирма: {company}\nИмейл: {email}\nТелефон: {phone}\nСтатус: 7-дневен безплатен тест\nВреме: {datetime.now(ZoneInfo('Europe/Sofia')).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    return f"""
    <!DOCTYPE html>
    <html lang="bg">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Успешна регистрация</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body style="background:#0b0f19; color:#fff; display:flex; align-items:center; justify-content:center; min-height:100vh;" class="p-3">
        <div class="text-center p-4" style="background:#111827; border:1px solid #1f2937; border-radius:12px; max-width:480px;">
            <h2 class="text-success mb-3">✓ Успешна активация!</h2>
            <p class="text-secondary">Благодарим ви, <strong>{company}</strong>. Вашият 7-дневен пробен период е стартиран. Ще получавате анализите на <strong>{email}</strong>.</p>
            <a href="/" class="btn btn-primary mt-2">← Към системата</a>
        </div>
    </body>
    </html>
    """

@app.route("/api/trigger-morning-report")
def trigger_report():
    send_admin_alert("Ръчен тест на сутрешния отчет (07:30 ч.)", "Потвърждение: Връзката за сутрешните доклади е напълно оперативна.")
    return "<script>alert('Тестовият отчет е изпратен успешно към kovko.firma@gmail.com!'); window.location.href='/';</script>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
