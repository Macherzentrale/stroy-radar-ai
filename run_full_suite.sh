#!/bin/bash
echo "[*] Стартиране на Stroy Radar Enterprise Suite..."

python cross_registry_scraper.py
python market_benchmark_engine.py
python roi_underwriter.py
python pdf_memorandum_engine.py
python email_alerts.py

echo "[✓] Пълният институционален цикъл и изпращането на имейли приключиха."
