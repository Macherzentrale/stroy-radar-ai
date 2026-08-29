import smtplib
import os
import glob
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# Настройки за изпращане (За тест може да се ползва Gmail App Password)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"  # 16-цифрена парола за приложения от Google

# Списък с активни платени абонати
SUBSCRIBERS = [
    {"name": "Адв. Георгиев", "email": "client1@example.com", "plan": "Executive Risk"},
    {"name": "Димитър Иванов (Инвеститор)", "email": "client2@example.com", "plan": "CHSI Deals"}
]

def find_latest_report():
    """Намира най-новия генериран Excel файл в директорията."""
    files = glob.glob("Executive_Risk_Report_*.xlsx")
    if not files:
        return None
    return max(files, key=os.path.getctime)

def send_weekly_reports(dry_run=True):
    latest_file = find_latest_report()
    if not latest_file:
        print("[!] Не е намерен генериран Excel отчет за изпращане.")
        return

    print("=" * 60)
    print(f"📧 СТАРТИРАНЕ НА ИМЕЙЛ ДИСТРИБУТОРА")
    print(f"📎 Прикачен файл: {latest_file}")
    print("=" * 60)

    for sub in SUBSCRIBERS:
        recipient = sub["email"]
        name = sub["name"]
        
        # Създаване на имейл съобщението
        msg = MIMEMultipart()
        msg["From"] = f"B2B Risk Radar <{SENDER_EMAIL}>"
        msg["To"] = recipient
        msg["Subject"] = f"📊 Седмичен риск бюлетин & ЧСИ мониторинг [{datetime.now().strftime('%d.%m.%Y')}]"

        body = f"""Здравейте, {name},

Прикачен ще намерите най-новия структуриран седмичен отчет за нововписани запори, ликвидации и изгодни ЧСИ публични търгове.

Основни акценти в броя:
- Пълна извадка на дружества с наложени обезпечителни мерки.
- AI Скоринг на реални имоти под пазарна ликвидационна стойност.
- Директни активни връзки към партидите в регистрите.

Файлът е оптимизиран за бърз филтър и анализ от правни и финансови екипи.

Поздрави,
Екипът на B2B Risk Radar
"""
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Прикачване на Excel файла
        with open(latest_file, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(latest_file)}",
            )
            msg.attach(part)

        if dry_run:
            print(f"[DEMO РЕЖИМ] Имейлът за {name} ({recipient}) е валидиран и готов за изпращане.")
        else:
            try:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
                server.quit()
                print(f"[✓] Изпратен успешно до: {recipient}")
            except Exception as e:
                print(f"[!] Грешка при изпращане до {recipient}: {e}")

    print("\n[✓] Дистрибуционният цикъл приключи.")

if __name__ == "__main__":
    # По подразбиране е в dry_run=True режим за безопасен тест без въведени реални пароли
    send_weekly_reports(dry_run=True)
