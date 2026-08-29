import sqlite3

DB_NAME = "stroy_radar_intel.db"

# Индикативни средни пазарни нива (€/кв.м) по сегменти
MARKET_BENCHMARKS = {
    "София": {"Жилищен имот": 1850.0, "Търговски обект": 2100.0, "Индустриален / Парцел": 650.0},
    "Пловдив": {"Жилищен имот": 1250.0, "Търговски обект": 1400.0, "Индустриален / Парцел": 450.0},
    "Варна": {"Жилищен имот": 1450.0, "Търговски обект": 1600.0, "Индустриален / Парцел": 500.0},
    "Бургас": {"Жилищен имот": 1200.0, "Търговски обект": 1350.0, "Индустриален / Парцел": 400.0},
    "България (Общо)": {"Жилищен имот": 950.0, "Търговски обект": 1050.0, "Индустриален / Парцел": 300.0}
}

def enrich_with_market_benchmarks():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Добавяне на нови финансови колони в таблицата, ако не съществуват
    try:
        cursor.execute("ALTER TABLE auctions ADD COLUMN market_avg_sqm_eur REAL")
        cursor.execute("ALTER TABLE auctions ADD COLUMN discount_percentage REAL")
        cursor.execute("ALTER TABLE auctions ADD COLUMN est_gross_profit_eur REAL")
    except sqlite3.OperationalError:
        pass  # Колоните вече съществуват

    cursor.execute("SELECT id, city, property_type, area_sqm, price_eur, price_sqm_eur FROM auctions")
    rows = cursor.fetchall()

    for r in rows:
        auc_id, city, prop_type, area_sqm, price_eur, price_sqm_eur = r
        
        city_benchmarks = MARKET_BENCHMARKS.get(city, MARKET_BENCHMARKS["България (Общо)"])
        market_sqm_eur = city_benchmarks.get(prop_type, 900.0)
        
        if area_sqm > 0 and price_sqm_eur > 0:
            est_market_total_eur = market_sqm_eur * area_sqm
            discount_pct = round(((est_market_total_eur - price_eur) / est_market_total_eur) * 100, 1)
            gross_profit_eur = round(est_market_total_eur - price_eur, 2)
        else:
            discount_pct = 0.0
            gross_profit_eur = 0.0

        cursor.execute("""
            UPDATE auctions 
            SET market_avg_sqm_eur = ?, discount_percentage = ?, est_gross_profit_eur = ?
            WHERE id = ?
        """, (market_sqm_eur, discount_pct, gross_profit_eur, auc_id))

    conn.commit()
    conn.close()
    print("[✓] Базата данни е обогатена с пазарни бенчмаркове и инвестиционни маржове.")

if __name__ == "__main__":
    enrich_with_market_benchmarks()
