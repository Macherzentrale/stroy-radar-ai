import time
import os
from datetime import datetime

TARGET_HOUR = 7
TARGET_MINUTE = 30

def run_daily_cycle():
    print("\n" + "=" * 60)
    print(f"⏰ СТАРТИРАНЕ НА ЕЖЕДНЕВЕН АВТОНОМЕН ЦИКЪЛ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. Изпълнение на главния пайплайн (Извличане + AI Скоринг + Excel)
    os.system("python main_pipeline.py")
    
    # 2. Автоматично изпращане по имейл на новия брой
    os.system("python email_delivery_engine.py")
    
    print("[✓] Ежедневният цикъл приключи успешно. Системата чака следващия график.\n")

def start_daemon():
    print("=" * 60)
    print(" 🤖 B2B RISK RADAR — 24/7 AUTONOMOUS BACKGROUND DAEMON")
    print(f" ⏳ График: Всеки ден в {TARGET_HOUR:02d}:{TARGET_MINUTE:02d} ч.")
    print("=" * 60)
    
    last_run_day = None
    
    while True:
        now = datetime.now()
        current_day = now.date()
        
        # Проверка дали е настъпил часът за изпълнение и дали не е пускан вече днес
        if now.hour == TARGET_HOUR and now.minute == TARGET_MINUTE and last_run_day != current_day:
            run_daily_cycle()
            last_run_day = current_day
            time.sleep(60)  # Изчакване 1 минута, за да не се повтори веднага
            
        time.sleep(10)  # Проверка на всеки 10 секунди

if __name__ == "__main__":
    start_daemon()
