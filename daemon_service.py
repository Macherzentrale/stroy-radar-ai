import time
import subprocess
from datetime import datetime

SCAN_INTERVAL_SECONDS = 21600  # На всеки 6 часа

def run_pipeline():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now}] === СТАРТИРАНЕ НА АВТОНОМЕН ПАЙПЛАЙН ===")
    
    scripts = [
        "cross_registry_scraper.py",
        "market_benchmark_engine.py",
        "roi_underwriter.py",
        "pdf_memorandum_engine.py",
        "email_alerts.py"
    ]
    
    for script in scripts:
        try:
            print(f"[*] Изпълнение на: {script}...")
            subprocess.run(["python", script], check=True)
        except Exception as e:
            print(f"[-] Грешка при {script}: {e}")

if __name__ == "__main__":
    print("[✓] Stroy Radar Autonomous Daemon е активен.")
    while True:
        run_pipeline()
        print(f"[*] Спящ режим до следващия цикъл (интервал: 6 часа)...")
        time.sleep(SCAN_INTERVAL_SECONDS)
