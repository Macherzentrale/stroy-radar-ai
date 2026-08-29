import os
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
DB_PATH = "stroy_radar_intel.db"

def send_admin_alert(subject, content):
    sender = os.environ.get("SENDER_EMAIL", "kovko.firma@gmail.com")
    password = os.environ.get("SENDER_APP_PASSWORD", "")
    admin_target = "kovko.firma@gmail.com"

    if not password:
        print(f"[Admin Alert] Липсва парола за изпращане. Нотификация: {subject}")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = f"Stroy Radar System <{sender}>"
        msg["To"] = admin_target
        msg["Subject"] = f"⚡ [Stroy Radar Alert] {subject}"
        msg.attach(MIMEText(content, "plain", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, admin_target, msg.as_string())
        server.quit()
        print(f"[✓] Изпратено известие до админа ({admin_target})!")
    except Exception as e:
        print(f"[!] Грешка при изпращане на админ известие: {e}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bg">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stroy Radar AI - Платформа за мониторинг</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .hero-card { background: #1e293b; border-radius: 16px; border: 1px solid #334155; padding: 2rem; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .admin-card { background: #1e293b; border-radius: 16px; border: 1px solid #3b82f6; padding: 2rem; margin-top: 2rem; }
        .btn-primary { background: #2563eb; border: none; font-weight: 600; padding: 0.75rem 1.5rem; border-radius: 8px; }
        .btn-primary:hover { background: #1d4ed8; }
        .badge-status { font-size: 0.85rem; padding: 0.4rem 0.8rem; border-radius: 6px; }
        .table-dark { background: #0f172a; }
    </style>
</head>
<body class="p-3 p-md-5">
    <div class="container">
        <!-- Клиентска зона за 7-дневен тест -->
        <div class="hero-card mb-5">
            <div class="row align-items-center">
                <div class="col-lg-7">
                    <span class="badge bg-primary mb-2">B2B Строителен Радар</span>
                    <h1 class="fw-bold mb-3">Автоматичен мониторинг на строителни обекти и ЧСИ търгове</h1>
                    <p class="text-secondary lead">Получавайте първи данни за новоиздадени разрешителни за строеж, парцели под себестойност и директни контакти на инвеститори.</p>
                    <ul class="list-unstyled text-light">
                        <li>✓ 7 дни пълен безплатен достъп</li>
                        <li>✓ Ежедневен сутрешен анализ в 07:30 ч.</li>
                        <li>✓ Пълен достъп до регистрите в реално време</li>
                    </ul>
                </div>
                <div class="col-lg-5">
                    <div class="card bg-dark border-secondary p-4 text-light">
                        <h4 class="fw-bold mb-3 text-center">Активирай 7 дни тест</h4>
                        <form action="/api/register-trial" method="POST">
                            <div class="mb-3">
                                <label class="form-label">Фирма / Инвеститор:</label>
                                <input type="text" name="company" class="form-control bg-secondary text-light border-0" placeholder="напр. Главболгарстрой ООД" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Имейл за достъп:</label>
                                <input type="email" name="email" class="form-control bg-secondary text-light border-0" placeholder="office@company.com" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Телефон:</label>
                                <input type="text" name="phone" class="form-control bg-secondary text-light border-0" placeholder="0888 123 456" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100 mt-2">Стартирай безплатен пробен период</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <!-- Админ панел за наблюдение на лидовете -->
        <div class="admin-card">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h3 class="fw-bold mb-0">📊 Админ Панел: Лидове и Кампании</h3>
                    <small class="text-secondary">Автоматично синхронизиран списък с целеви контакти</small>
                </div>
                <a href="/api/trigger-morning-report" class="btn btn-outline-info btn-sm">⚡ Тествай изпращане на сутрешен отчет</a>
            </div>

            <div class="table-responsive">
                <table class="table table-dark table-hover align-middle">
                    <thead>
                        <tr class="text-secondary">
                            <th>#</th>
                            <th>Фирма / Контакт</th>
                            <th>Имейл</th>
                            <th>Статус на офертата</th>
                            <th>Последно действие</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for lead in leads %}
                        <tr>
                            <td>{{ lead[0] }}</td>
                            <td class="fw-bold">{{ lead[2] }}</td>
                            <td><code>{{ lead[1] }}</code></td>
                            <td>
                                {% if lead[3] == 'sent' %}
                                    <span class="badge bg-success badge-status">Изпратена оферта</span>
                                {% elif lead[3] == 'trial_active' %}
                                    <span class="badge bg-warning text-dark badge-status">🌟 Активен 7-дневен тест</span>
                                {% else %}
                                    <span class="badge bg-secondary badge-status">Чакащ</span>
                                {% endif %}
                            </td>
                            <td class="text-secondary">{{ lead[4] if lead[4] else '—' }}</td>
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

@app.route("/")
def home():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, company_name, status, sent_at FROM leads_outreach ORDER BY id DESC LIMIT 50")
    leads = c.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, leads=leads)

@app.route("/api/register-trial", methods=["POST"])
def register_trial():
    company = request.form.get("company")
    email = request.form.get("email")
    phone = request.form.get("phone")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO leads_outreach (email, company_name, status, sent_at) VALUES (?, ?, 'trial_active', CURRENT_TIMESTAMP)", (email, company))
    conn.commit()
    conn.close()

    # Изпращаме моментално известие на вашия имейл
    send_admin_alert(
        subject=f"Нов 7-дневен тест: {company}",
        content=f"Честито! Имате нова регистрация за пробен период:\n\nФирма: {company}\nИмейл: {email}\nТелефон: {phone}\nСтатус: 7-дневен безплатен тест"
    )

    return f"""
    <div style="background:#0f172a; color:#fff; height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:sans-serif; text-align:center;">
        <h1 style="color:#22c55e;">✓ Вашият 7-дневен безплатен достъп е активиран!</h1>
        <p style="color:#94a3b8; max-width:500px;">Благодарим ви, {company}. Ще получавате ежедневните бюлетини и анализи на {email}.</p>
        <a href="/" style="color:#38bdf8; margin-top:20px; text-decoration:none;">← Обратно към началната страница</a>
    </div>
    """

@app.route("/api/trigger-morning-report")
def trigger_report():
    send_admin_alert("Ръчно пуснат тестов сутрешен отчет", "Това е тестово потвърждение, че имейл връзката за сутрешните доклади в 07:30 ч. работи безупречно.")
    return "<script>alert('Тестовият отчет е изпратен към kovko.firma@gmail.com!'); window.location.href='/';</script>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
