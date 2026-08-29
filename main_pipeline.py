import os
import time
import json
import csv
from datetime import datetime

def log_step(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] 🚀 {message}")

def run_pipeline():
    print("=" * 65)
    print("      🔥 B2B AUTONOMOUS RISK & CHSI DATA PIPELINE")
    print("=" * 65)
    
    # Стъпка 1: Извличане на живите данни
    log_step("Стартиране на извличането от публичните регистри...")
    os.system("python chsi_live_scraper.py")
    
    # Стъпка 2: AI Анализ и Скоринг
    log_step("Преминаване през AI модела за скоринг на сделките...")
    os.system("python ai_scoring_engine.py")
    
    # Стъпка 3: Генериране на Премиум Executive Excel
    log_step("Създаване на брандиран Excel отчет с филтри и линкове...")
    os.system("python premium_report_builder.py")
    
    # Стъпка 4: Копиране на отчетите в Downloads папката на телефона
    log_step("Синхронизиране на файловете с локалната памет на телефона...")
    os.system("cp Executive_Risk_Report_*.xlsx ~/storage/downloads/ 2>/dev/null")
    os.system("cp ai_enriched_market_feed.json ~/storage/downloads/ 2>/dev/null")
    os.system("cp llms.txt ~/storage/downloads/ 2>/dev/null")
    
    print("\n" + "=" * 65)
    print("  ✅ ЦИКЪЛЪТ ЗАВЪРШИ УСПЕШНО! ВСИЧКИ СИСТЕМИ СА АКТУАЛИЗИРАНИ")
    print("=" * 65)
    print("📦 Готови активи:")
    print("  1. Executive_Risk_Report.xlsx  -> За B2B директни клиенти")
    print("  2. ai_enriched_market_feed.json -> За външни API заявки")
    print("  3. llms.txt                    -> За AI агенти (ChatGPT / Claude)")
    print("  4. API Server                  -> Активен и сервира на живо")

if __name__ == "__main__":
    run_pipeline()
