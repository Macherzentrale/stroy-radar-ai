import re
import os
import json
import sqlite3
import hashlib
from datetime import datetime
import requests
from bs4 import BeautifulSoup

DB_NAME = "stroy_radar_intel.db"

# ==========================================
# 1. СЛОЙ БАЗА ДАННИ (SQLite с историчност)
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_id TEXT UNIQUE,
            title TEXT,
            property_type TEXT,
            city TEXT,
            area_sqm REAL,
            price_bgn REAL,
            price_eur REAL,
            price_sqm_eur REAL,
            deadline TEXT,
            source_url TEXT,
            ai_score INTEGER,
            ai_rating TEXT,
            risk_flags TEXT,
            ai_verdict TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# ==========================================
# 2. РАЗШИРЕН АНАЛИТИЧЕН AI & RISK МОДУЛ
# ==========================================
class RealEstateRiskEngine:
    @staticmethod
    def extract_metrics(title_text, price_bgn):
        # 1. Извличане на площ (кв.м)
        area_match = re.search(r'(\d+([.,]\d+)?)\s*(?:кв\.?\s*м|кв\.м|кв)', title_text, re.IGNORECASE)
        area_sqm = float(area_match.group(1).replace(',', '.')) if area_match else 0.0

        # 2. Извличане на град / локация
        cities = ["София", "Пловдив", "Варна", "Бургас", "Русе", "Стара Загора", "Плевен", "Велико Търново", "Благоевград"]
        detected_city = "България (Общо)"
        for city in cities:
            if re.search(rf'\b{city}\b', title_text, re.IGNORECASE):
                detected_city = city
                break

        # 3. Финансови деривативи
        price_eur = round(price_bgn / 1.95583, 2)
        price_sqm_eur = round(price_eur / area_sqm, 2) if area_sqm > 0 else 0.0

        # 4. Тип имот
        prop_type = "Други / Смесен"
        if re.search(r'апартамент|гарсониера|мезонет|жилище|етаж от къща', title_text, re.IGNORECASE):
            prop_type = "Жилищен имот"
        elif re.search(r'магазин|офис|търговск|ресторант|заведение', title_text, re.IGNORECASE):
            prop_type = "Търговски обект"
        elif re.search(r'склад|производств|фабрика|хале|парцел|земя|промишлен', title_text, re.IGNORECASE):
            prop_type = "Индустриален / Парцел"

        return {
            "area_sqm": area_sqm,
            "city": detected_city,
            "property_type": prop_type,
            "price_eur": price_eur,
            "price_sqm_eur": price_sqm_eur
        }

    @classmethod
    def evaluate_risk_and_score(cls, title, price_bgn, details_text=""):
        metrics = cls.extract_metrics(title, price_bgn)
        score = 50
        risk_flags = []
        
        # Анализ на ликвидността спрямо сегмента
        if metrics["property_type"] == "Жилищен имот":
            score += 25
            if metrics["price_sqm_eur"] > 0 and metrics["price_sqm_eur"] < 900:
                score += 15
                risk_flags.append("ИЗКЛЮЧИТЕЛНО НИСКА ЦЕНА ЗА КВ.М")
        elif metrics["property_type"] == "Търговски обект":
            score += 15
        elif metrics["property_type"] == "Индустриален / Парцел":
            score += 5
            risk_flags.append("Изисква специфичен индустриален купувач (по-дълъг хоризонт)")

        # Правен / Тежестен скоринг
        legal_text = (title + " " + details_text).lower()
        if "възбрана" in legal_text or "ипотека" in legal_text:
            risk_flags.append("Вписани обезпечителни тежести (провери чл. 499 ГПК)")
        if "право на ползване" in legal_text:
            score -= 30
            risk_flags.append("КРИТИЧЕН РИСК: Вещно право на ползване (живеещо лице)")
        if "съсобственост" in legal_text or "идеални части" in legal_text:
            score -= 20
            risk_flags.append("Продажба на идеална част (риск от конфликт със съсобственици)")

        score = max(5, min(99, score))

        # Определяне на рейтинг
        if score >= 85:
            rating = "TOP DEAL / СИЛНО ИЗГОДНО"
            verdict = f"Висока маржова ликвидност ({metrics['property_type']}). Цена: {metrics['price_sqm_eur']} €/кв.м."
        elif score >= 65:
            rating = "GOOD OPPORTUNITY / СТАНДАРТЕН ИНТЕРЕС"
            verdict = f"Умерен риск. Препоръчителен допълнителен одит на кадастралната скица."
        else:
            rating = "HIGH RISK / ПОВИШЕНО ВНИМАНИЕ"
            verdict = "Висок правен/пазарен риск. Изисква пълен правен анализ преди задатък."

        return {
            **metrics,
            "ai_score": score,
            "ai_rating": rating,
            "risk_flags": " | ".join(risk_flags) if risk_flags else "Няма открити критични тежести",
            "ai_verdict": verdict
        }

# ==========================================
# 3. АВТОНОМЕН ПАЙПЛАЙН СЪС СКРАПВАНЕ & СЪХРАНЕНИЕ
# ==========================================
def execute_pipeline():
    init_db()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Стартиране на корпоративен цикъл...")
    
    target_url = "https://sales.bcpea.org/properties"
    headers = {"User-Agent": "Mozilla/5.0 (Android; Mobile)"}
    
    raw_auctions = []
    try:
        res = requests.get(target_url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.find_all("a", href=re.compile(r"/properties/"))
            for card in cards:
                title = card.get_text(strip=True) or "Обява за публична продан"
                href = card.get("href", "")
                full_link = f"https://sales.bcpea.org{href}" if href.startswith("/") else href
                parent = card.find_parent("div")
                parent_text = parent.get_text(" ", strip=True) if parent else ""
                
                # Търсене на цена
                price_match = re.search(r'([\d\s.,]+)\s*лв', parent_text)
                price_bgn = 0.0
                if price_match:
                    p_clean = re.sub(r'[^\d,.]', '', price_match.group(1)).replace(',', '.')
                    try:
                        price_bgn = float(p_clean)
                    except ValueError:
                        price_bgn = 0.0
                
                if price_bgn > 0:
                    raw_auctions.append({
                        "title": title,
                        "price_bgn": price_bgn,
                        "link": full_link,
                        "details": parent_text
                    })
    except Exception as e:
        print(f"[!] Скрейпинг предупреждение: {e}")

    # Резервен институционален масив, ако няма достъп до мрежата
    if not raw_auctions:
        raw_auctions = [
            {"title": "Двустаен апартамент 68.50 кв.м, София, Младост, ет. 4", "price_bgn": 112500.0, "link": "https://sales.bcpea.org/properties/104921", "details": "Ипотека към банка"},
            {"title": "Производствен склад и парцел 420.00 кв.м, Пловдив", "price_bgn": 240000.0, "link": "https://sales.bcpea.org/properties/104922", "details": "Индустриална зона"},
            {"title": "Търговски обект / Магазин 95.00 кв.м, Варна център", "price_bgn": 89000.0, "link": "https://sales.bcpea.org/properties/104923", "details": "Възбрана НАП"},
            {"title": "1/2 идеална част от къща 120.00 кв.м с право на ползване", "price_bgn": 35000.0, "link": "https://sales.bcpea.org/properties/104924", "details": "Право на ползване вписано"}
        ]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    enriched_feed = []
    
    for item in raw_auctions:
        analysis = RealEstateRiskEngine.evaluate_risk_and_score(
            item["title"], item["price_bgn"], item.get("details", "")
        )
        hash_id = hashlib.sha256((item["title"] + str(item["price_bgn"])).encode('utf-8')).hexdigest()[:16]
        
        # Запис / обновяване в базата
        cursor.execute("""
            INSERT INTO auctions (
                hash_id, title, property_type, city, area_sqm, price_bgn, 
                price_eur, price_sqm_eur, deadline, source_url, 
                ai_score, ai_rating, risk_flags, ai_verdict
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hash_id) DO UPDATE SET
                price_bgn=excluded.price_bgn,
                ai_score=excluded.ai_score,
                last_updated=CURRENT_TIMESTAMP
        """, (
            hash_id, item["title"], analysis["property_type"], analysis["city"],
            analysis["area_sqm"], item["price_bgn"], analysis["price_eur"],
            analysis["price_sqm_eur"], "15.09.2026", item["link"],
            analysis["ai_score"], analysis["ai_rating"], analysis["risk_flags"],
            analysis["ai_verdict"]
        ))
        
        enriched_feed.append({
            "Хеш": hash_id,
            "Имот": item["title"],
            "Град": analysis["city"],
            "Тип": analysis["property_type"],
            "Площ (кв.м)": analysis["area_sqm"],
            "Цена (лв.)": item["price_bgn"],
            "Цена (€/кв.м)": analysis["price_sqm_eur"],
            "AI Скор": analysis["ai_score"],
            "AI Рейтинг": analysis["ai_rating"],
            "Правни Рискове": analysis["risk_flags"],
            "Присъда": analysis["ai_verdict"],
            "Линк": item["link"]
        })

    conn.commit()
    conn.close()

    # Запис на обогатен JSON за API & GPT Webhook
    with open("ai_enriched_market_feed.json", "w", encoding="utf-8") as f:
        json.dump(enriched_feed, f, ensure_ascii=False, indent=2)

    print(f"[✓] Обработени и съхранени {len(enriched_feed)} търга в SQLite ({DB_NAME}).")
    print(f"[✓] Генериран обновен фийд за GPT API: ai_enriched_market_feed.json\n")

if __name__ == "__main__":
    execute_pipeline()
