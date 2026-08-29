import os
import json
import smtplib
import time
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DB_PATH = "stroy_radar_intel.db"
CONFIG_FILE = "email_config.json"

def get_email_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": os.environ.get("SENDER_EMAIL", "kovko.firma@gmail.com"),
        "sender_password": os.environ.get("SENDER_APP_PASSWORD", "")
    }

def init_outreach_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leads_outreach (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            company_name TEXT,
            status TEXT DEFAULT 'pending',
            sent_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def send_outreach_campaign():
    config = get_email_config()
    sender = config.get("sender_email")
    password = config.get("sender_password")

    if not sender or not password:
        print("[Outreach] Липсва конфигуриран имейл или парола на приложението (App Password).")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, email, company_name FROM leads_outreach WHERE status = 'pending' LIMIT 20")
    leads = c.fetchall()

    if not leads:
        print("[Outreach] Няма чакащи нови лидове за изпращане.")
        conn.close()
        return

    try:
        server = smtplib.SMTP(config.get("smtp_server", "smtp.gmail.com"), config.get("smtp_port", 587))
        server.starttls()
        server.login(sender, password)

        for lead_id, email, company in leads:
            name = company if company else "колеги"
            subject = "Автоматичен мониторинг на строителни обекти и ЧСИ търгове (7 дни безплатен достъп)"
            
            body = f"""Здравейте, {name},

Обръщаме се към вас като активен участник в строително-инвестиционния сектор.

Разработихме платформата Stroy Radar AI — специализиран софтуер за автоматичен мониторинг на:
1. Всички новоиздадени разрешителни за строеж в страната.
2. Публични търгове от ЧСИ за имоти и парцели под пазарна цена.
3. Анализ на риска и финансова оценка на инвестиционни възможности.

За да видите реалните възможности за вашия бизнес, сме активирали 7-дневен пълен безплатен тестов период:
👉 Вход в платформата: https://stroy-radar-ai.onrender.com

След пробния период можете да изберете подходящ абонаментен план за достъп до пълната база данни и автоматичните известия.

Поздрави,
Екипът на Stroy Radar AI
Имейл: {sender}
"""
            msg = MIMEMultipart()
            msg["From"] = f"Stroy Radar AI <{sender}>"
            msg["To"] = email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain", "utf-8"))

            try:
                server.sendmail(sender, email, msg.as_string())
                c.execute("UPDATE leads_outreach SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?", (lead_id,))
                conn.commit()
                print(f"[✓] Изпратен имейл към: {email} ({name})")
                time.sleep(15)  # 15 секунди пауза между имейлите за безопасност
            except Exception as send_err:
                print(f"[!] Грешка при изпращане към {email}: {send_err}")
                c.execute("UPDATE leads_outreach SET status = 'failed' WHERE id = ?", (lead_id,))
                conn.commit()

        server.quit()
    except Exception as e:
        print(f"[!] SMTP грешка: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_outreach_db()
    send_outreach_campaign()
