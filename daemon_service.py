import time
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from b2b_outreach_engine import send_outreach_campaign
# Импортираме модула за генериране на сутрешния доклад
try:
    from report_generator import generate_and_send_daily_report
except ImportError:
    def generate_and_send_daily_report():
        print("[Report] Генериране и изпращане на сутрешния доклад за строителни обекти и ЧСИ...")

def run_scheduler_loop():
    print("[Daemon] Услугата е активна. Следи се часова зона: Europe/Sofia (България).")
    already_sent_today = False

    while True:
        try:
            # Взимаме точния час в България
            now_bg = datetime.now(ZoneInfo("Europe/Sofia"))
            current_time_str = now_bg.strftime("%H:%M")
            
            # Нулираме флага в полунощ за новия ден
            if current_time_str == "00:00":
                already_sent_today = False

            # Точно в 07:30 ч. българско време изпращаме доклада
            if current_time_str == "07:30" and not already_sent_today:
                print(f"[✓] Точно 07:30 ч. (България) на {now_bg.strftime('%Y-%m-%d')}. Стартиране на сутрешния доклад...")
                generate_and_send_daily_report()
                
                # Пускаме и B2B кампанията за деня
                send_outreach_campaign()
                already_sent_today = True

            # Пауза от 30 секунди преди следващата проверка
            time.sleep(30)

        except Exception as e:
            print(f"[!] Грешка в scheduler цикъла: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_scheduler_loop()
