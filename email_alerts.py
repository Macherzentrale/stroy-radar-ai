import sqlite3
import smtplib
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

DB_NAME = "stroy_radar_intel.db"
CONFIG_FILE = "email_config.json"

def send_email_digest():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT hash_id, title, city, area_sqm, price_eur, 
               discount_percentage, net_profit_eur, net_roi_percent, ai_score, 
               ai_rating, risk_flags, deadline, source_url
        FROM auctions
        WHERE ai_score >= ?
        ORDER BY ai_score DESC
    """, (cfg.get("min_score_alert", 80),))
    deals = c.fetchall()
    conn.close()

    if not deals:
        print("[*] Няма оферти за изпращане.")
        return

    items_html = ""
    for d in deals:
        items_html += f"""
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-bottom:12px;">
            <div style="font-size:12px;color:#10b981;font-weight:bold;">★ AI СКОР {d[8]}/100 ({d[9]}) | Град: {d[2]}</div>
            <h3 style="margin:6px 0;font-size:15px;color:#0f172a;">{d[1]}</h3>
            <p style="margin:4px 0;font-size:13px;color:#64748b;">Площ: {d[3]} кв.м | Срок: <b>{d[11] or 'Виж обявление'}</b></p>
            <p style="margin:4px 0;font-size:13px;"><b>Тръжна цена:</b> {d[4]:,.2f} € (-{d[5]}%)</p>
            <p style="margin:4px 0;font-size:13px;color:#10b981;"><b>Net ROI:</b> +{d[6]:,.2f} € ({d[7]}%)</p>
            <p style="margin:4px 0;font-size:12px;color:#ef4444;"><b>Тежести:</b> {d[10]}</p>
            <a href="{d[12]}" style="display:inline-block;background:#0284c7;color:#fff;padding:6px 12px;text-decoration:none;border-radius:4px;font-size:12px;margin-top:8px;">Отвори досието ↗</a>
        </div>
        """

    full_html = f"""
    <html>
    <body style="font-family:sans-serif;background:#f1f5f9;padding:16px;">
        <div style="max-width:600px;margin:auto;">
            <div style="background:#0f172a;color:#00f2a1;padding:16px;text-align:center;font-weight:bold;font-size:18px;">
                STROY RADAR AI | ТОП ОФЕРТИ
            </div>
            <div style="padding:16px;background:#f8fafc;border:1px solid #cbd5e1;">
                {items_html}
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Stroy Radar AI Alert - {len(deals)} TOP Deals"
    msg["From"] = cfg["sender_email"]
    msg["To"] = cfg["recipient_email"]
    msg.attach(MIMEText(full_html, "html", "utf-8"))

    try:
        server = smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"]))
        server.starttls()
        pwd = str(cfg["sender_app_password"]).replace(" ", "").strip()
        server.login(cfg["sender_email"], pwd)
        server.sendmail(cfg["sender_email"], cfg["recipient_email"], msg.as_string())
        server.quit()
        print(f"[✓] УСПЕШНО ИЗПРАТЕН ИМЕЙЛ ДО: {cfg['recipient_email']}")
    except Exception as e:
        print(f"[-] Грешка: {e}")

if __name__ == "__main__":
    send_email_digest()
