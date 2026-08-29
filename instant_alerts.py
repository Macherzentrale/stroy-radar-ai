import sqlite3
import requests
import json
import os

DB_NAME = "stroy_radar_intel.db"
CONFIG_FILE = "alert_config.json"

# Базова конфигурация (попълва се при интеграция с Telegram)
DEFAULT_CONFIG = {
    "telegram_bot_token": "",  # Поставете вашия токен от @BotFather
    "telegram_chat_id": "",    # Вашият Chat ID от @userinfobot
    "min_score_alert": 85,
    "enabled": False
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def send_telegram_alert(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"[-] Грешка при изпращане: {e}")
        return False

def check_and_dispatch_alerts():
    cfg = load_config()
    if not cfg.get("enabled") or not cfg.get("telegram_bot_token"):
        print("[!] Модулът за известия е в режим СТАНДАРТ (Локално записване).")
        print("[!] За Push известия в Telegram въведете Token и Chat ID в 'alert_config.json'.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT hash_id, title, city, price_eur, discount_percentage, net_profit_eur, net_roi_percent, ai_score, source_url
        FROM auctions
        WHERE ai_score >= ?
    """, (cfg.get("min_score_alert", 85),))
    deals = c.fetchall()
    conn.close()

    print(f"[*] Открити {len(deals)} TOP актива за изпращане...")
    for d in deals:
        msg = (
            f"🚨 <b>STROY RADAR AI | TOP DEAL ALERT</b> 🚨\n\n"
            f"🏢 <b>Имот:</b> {d[1]}\n"
            f"📍 <b>Град:</b> {d[2]}\n"
            f"💰 <b>Тръжна цена:</b> {d[3]:,.2f} € (<b>-{d[4]}%</b> под пазара)\n"
            f"📈 <b>Прогнозен Net ROI:</b> +{d[5]:,.2f} € (<b>{d[6]}%</b>)\n"
            f"★ <b>AI Скор:</b> <code>{d[7]}/100</code>\n\n"
            f"🔗 <a href='{d[8]}'>Отвори официалното ЧСИ досие</a>"
        )
        send_telegram_alert(cfg["telegram_bot_token"], cfg["telegram_chat_id"], msg)

if __name__ == "__main__":
    check_and_dispatch_alerts()
