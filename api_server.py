import os
import io
import csv
import sqlite3
import smtplib
import threading
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, render_template_string, Response

app = Flask(__name__)
DB_PATH = "stroy_radar_intel.db"

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
    conn.commit()
    conn.close()

init_db()

def send_email_msg(to_email, subject, body_text):
    sender = os.environ.get("SENDER_EMAIL", "kovko.firma@gmail.com")
    password = os.environ.get("SENDER_APP_PASSWORD", "")
    if not password:
        print(f"[Email Skipped - No Password] To: {to_email} | Subj: {subject}")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = f"Stroy Radar AI <{sender}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[!] Грешка при изпращане към {to_email}: {e}")
        return False

# --- Автоматична поредица за конверсии (Ден 5 и Ден 7) ---
def process_trial_followups():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, company_name, trial_start, last_followup_day FROM leads_outreach WHERE status = 'trial_active'")
    active_trials = c.fetchall()
    now_bg = datetime.now(ZoneInfo("Europe/Sofia"))

    for lead_id, email, company, trial_start_str, last_day in active_trials:
        if not trial_start_str:
            continue
        try:
            start_date = datetime.fromisoformat(trial_start_str.replace("Z", ""))
            days_passed = (now_bg.replace(tzinfo=None) - start_date).days
        except Exception:
            continue

        comp_name = company if company else "Колеги"

        # Ден 5: Подсещане и резултати
        if days_passed >= 5 and last_day < 5:
            subject = f"Остават 48 часа от безплатния ви тестов период - Stroy Radar AI"
            body = f"""Здравейте, {comp_name},

Остават точно 2 дни от вашия 7-дневен безплатен пробен период в Stroy Radar AI.

До момента системата анализира:
• Новоиздадените разрешителни за строеж за вашия район
• Актуалните публични търгове от ЧСИ за имоти и парцели под пазарна себестойност

За да запазите непрекъснат достъп до данните и сутрешните отчети в 07:30 ч., можете да изберете абонаментен план:
👉 План Старт: €49 / месец
👉 План Про: €99 / месец

Пълен преглед на платформата: https://stroy-radar-ai.onrender.com

Поздрави,
Екипът на Stroy Radar AI
"""
            if send_email_msg(email, subject, body):
                c.execute("UPDATE leads_outreach SET last_followup_day = 5 WHERE id = ?", (lead_id,))
                conn.commit()

        # Ден 7: Финално предложение за преминаване към абонамент
        elif days_passed >= 7 and last_day < 7:
            subject = f"Вашият 7-дневен тест изтече – изберете план за пълен достъп"
            body = f"""Здравейте, {comp_name},

Вашият 7-дневен безплатен тестов период в Stroy Radar AI приключи днес.

За да продължите да получавате:
1. Ежедневни сутрешни анализи на новите разрешителни за строеж
2. Сигнали за ЧСИ имоти на преференциални цени
3. Пълен експорт на контакти на инвеститори и строители

Изберете подходящия абонаментен план за вашата фирма:
• Старт (€49/мес) – Фокус върху 1 избран регион
• Про (€99/мес) – Цяла България + ЧСИ търгове и CSV експорт

Свържете се с нас за активация на платен абонамент: kovko.firma@gmail.com
Вход в платформата: https://stroy-radar-ai.onrender.com

Поздрави,
Екипът на Stroy Radar AI
"""
            if send_email_msg(email, subject, body):
                c.execute("UPDATE leads_outreach SET last_followup_day = 7, status = 'trial_expired' WHERE id = ?", (lead_id,))
                conn.commit()

    conn.close()

# --- Фонов таймер за 07:30 ч. сутринта ---
def background_daemon():
    print("[Daemon] Стартиран фонов процес (Europe/Sofia).")
    already_sent_today = False
    while True:
        try:
            now_bg = datetime.now(ZoneInfo("Europe/Sofia"))
            time_str = now_bg.strftime("%H:%M")

            if time_str == "00:00":
                already_sent_today = False

            if time_str == "07:30" and not already_sent_today:
                print(f"[✓] 07:30 ч. България. Обработка на сутрешен отчет и follow-up кампании...")
                send_email_msg(
                    "kovko.firma@gmail.com",
                    "Сутрешен бюлетин: Активност на системата и лидовете",
                    f"Автоматичен отчет за {now_bg.strftime('%d.%m.%Y')}.\nСистемата работи нормално."
                )
                process_trial_followups()
                already_sent_today = True

            time.sleep(30)
        except Exception as e:
            print(f"[Daemon Loop Error] {e}")
            time.sleep(60)

thread = threading.Thread(target=background_daemon, daemon=True)
thread.start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stroy Radar AI - Строителен и ЧСИ Мониторинг</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        .navbar { background: #111827; border-bottom: 1px solid #1f2937; }
        .card-custom { background: #111827; border: 1px solid #1f2937; border-radius: 12px; }
        .btn-brand { background: #2563eb; color: #fff; font-weight: 600; border-radius: 8px; }
        .btn-brand:hover { background: #1d4ed8; color: #fff; }
        .form-control { background: #1f2937 !important; border: 1px solid #374151 !important; color: #f9fafb !important; }
        .badge-trial { background: #eab308; color: #000; font-weight: 600; }
        .badge-expired { background: #ef4444; color: #fff; }
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
                    <li class="nav-item"><a class="nav-link" href="#pricing">Абонаменти (€)</a></li>
                    <li class="nav-item"><a class="nav-link" href="#admin-section">Админ Панел</a></li>
                    <li class="nav-item"><a href="/api/export-leads-csv" class="btn btn-outline-success btn-sm">📥 Експорт в Excel (CSV)</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="container py-4">
        <!-- Заглавен блок и регистрация -->
        <div class="row align-items-center g-4 py-4">
            <div class="col-lg-7">
                <span class="badge bg-primary-subtle text-primary mb-2 px-3 py-2">B2B Строителен Радар</span>
                <h1 class="display-6 fw-bold text-white mb-3">Мониторинг на строителни обекти и ЧСИ имоти</h1>
                <p class="text-secondary lead fs-6">Пълен достъп до новоиздадени разрешителни за строеж, търгове от ЧСИ и директни контакти на инвеститори в България.</p>
                <div class="row g-2 mt-2 text-light">
                    <div class="col-12 col-md-6">✓ 7 дни безплатен пробен достъп</div>
                    <div class="col-12 col-md-6">✓ Анализ и отчет всяка сутрин в 07:30 ч.</div>
                    <div class="col-12 col-md-6">✓ Експорт на контактите в Excel</div>
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

        <!-- Абонаментни планове в ЕВРО (€) -->
        <div id="pricing" class="py-5">
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
                            <li>✓ Достъп до контакти на инвеститори</li>
                        </ul>
                    </div>
                </div>
                <div class="col-md-5 col-lg-4">
                    <div class="card card-custom p-4 text-center h-100 border-primary">
                        <span class="badge bg-primary mb-2">Най-популярен</span>
                        <h5>Про</h5>
                        <h2 class="text-primary my-3">€99<small class="fs-6 text-secondary">/мес</small></h2>
                        <p class="text-secondary small">За строителни предприемачи, инвеститори и търговци.</p>
                        <ul class="list-unstyled text-start small mb-4">
                            <li>✓ Всички 28 области в България</li>
                            <li>✓ Разрешителни + ЧСИ търгове под пазарна цена</li>
                            <li>✓ Ежедневен сутрешен анализ в 07:30 ч.</li>
                            <li>✓ <strong>Неограничен експорт в Excel (CSV)</strong></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Админ Панел с Лидовете и Бутон за Експорт -->
        <div id="admin-section" class="card card-custom p-4 mt-4">
            <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mb-3">
                <div>
                    <h4 class="fw-bold mb-0">📊 Админ Панел: Управление на базата</h4>
                    <small class="text-secondary">Общо регистрирани B2B компании и статус на тестовите периоди</small>
                </div>
                <a href="/api/export-leads-csv" class="btn btn-success btn-sm">📥 Свали базата в Excel (CSV)</a>
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
                            <th>Тестов период от</th>
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
                                    <span class="badge badge-trial">🌟 Активен 7-дневен тест</span>
                                {% elif lead[4] == 'trial_expired' %}
                                    <span class="badge badge-expired">Изтекъл тест</span>
                                {% elif lead[4] == 'sent' %}
                                    <span class="badge bg-success">Изпратена оферта</span>
                                {% else %}
                                    <span class="badge bg-secondary">В базата</span>
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
    c.execute("SELECT id, email, company_name, phone, status, trial_start FROM leads_outreach ORDER BY id DESC LIMIT 50")
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

    # Известие до администратора
    send_email_msg(
        "kovko.firma@gmail.com",
        f"Нова регистрация за 7 дни тест: {company}",
        f"Нов потенциален клиент стартира тест:\n\nФирма: {company}\nИмейл: {email}\nТелефон: {phone}\nПлан: 7-дневен безплатен тест\nДата: {datetime.now(ZoneInfo('Europe/Sofia')).strftime('%d.%m.%Y %H:%M')}"
    )

    return f"""
    <!DOCTYPE html>
    <html lang="bg">
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Успешна активация</title><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet"></head>
    <body style="background:#0b0f19; color:#fff; display:flex; align-items:center; justify-content:center; min-height:100vh;" class="p-3">
        <div class="text-center p-4" style="background:#111827; border:1px solid #1f2937; border-radius:12px; max-width:480px;">
            <h2 class="text-success mb-3">✓ Успешна активация!</h2>
            <p class="text-secondary">Благодарим ви, <strong>{company}</strong>. Вашият 7-дневен тестов период е активен. Сутрешните отчети ще се изпращат на <strong>{email}</strong>.</p>
            <a href="/" class="btn btn-primary mt-2">← Към системата</a>
        </div>
    </body>
    </html>
    """

# --- Точка 3: CSV Експорт с UTF-8 BOM за Excel ---
@app.route("/api/export-leads-csv")
def export_leads_csv():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, company_name, email, phone, status, trial_start, created_at FROM leads_outreach ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    # UTF-8 BOM за автоматично разпознаване на кирилица в Excel
    output.write('\ufeff')
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["ID", "Име на фирма", "Имейл адрес", "Телефон", "Статус", "Начало на тестов период", "Дата на добавяне"])

    for r in rows:
        writer.writerow(r)

    csv_data = output.getvalue()
    filename = f"stroy_radar_leads_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
