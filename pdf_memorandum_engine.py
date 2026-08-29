import sqlite3
import os

DB_NAME = "stroy_radar_intel.db"
OUTPUT_DIR = "pdf_memos"

def generate_deal_sheets():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, hash_id, title, city, area_sqm, price_eur, net_profit_eur, net_roi_percent, ai_score, risk_flags, source_url FROM auctions WHERE ai_score >= 80")
    rows = c.fetchall()
    conn.close()

    for r in rows:
        memo = (
            f"=====================================================\n"
            f" STROY RADAR AI | ИНВЕСТИЦИОНЕН МЕМОРАНДУМ #{r[1]}\n"
            f"=====================================================\n"
            f"Имот: {r[2]}\n"
            f"Град: {r[3]} | Площ: {r[4]} кв.м\n"
            f"Тръжна цена: {r[5]:,.2f} EUR\n"
            f"Прогнозна чиста печалба: +{r[6]:,.2f} EUR (Net ROI: {r[7]}%)\n"
            f"AI Инвестиционен скор: {r[8]}/100\n"
            f"Правен статус / Рискове: {r[9]}\n"
            f"Официално досие: {r[10]}\n"
            f"=====================================================\n"
        )
        with open(os.path.join(OUTPUT_DIR, f"MEMO_{r[3]}_{r[0]}.txt"), "w", encoding="utf-8") as f:
            f.write(memo)
    print(f"[✓] Генерирани {len(rows)} институционални инвестиционни меморандума в '{OUTPUT_DIR}/'.")

if __name__ == "__main__":
    generate_deal_sheets()
