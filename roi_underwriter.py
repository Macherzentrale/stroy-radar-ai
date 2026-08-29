import sqlite3

DB_NAME = "stroy_radar_intel.db"

def calculate_net_roi():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Добавяне на финансовите метрики в схемата на базата
    cols_to_add = [
        ("total_acquisition_cost_eur", "REAL"),
        ("chsi_fees_eur", "REAL"),
        ("local_tax_eur", "REAL"),
        ("capex_est_eur", "REAL"),
        ("net_profit_eur", "REAL"),
        ("net_roi_percent", "REAL")
    ]
    for col_name, col_type in cols_to_add:
        try:
            cursor.execute(f"ALTER TABLE auctions ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
        SELECT id, property_type, area_sqm, price_eur, market_avg_sqm_eur 
        FROM auctions
    """)
    rows = cursor.fetchall()

    for r in rows:
        auc_id, prop_type, area_sqm, price_eur, market_avg_sqm_eur = r

        if price_eur > 0 and area_sqm > 0 and market_avg_sqm_eur > 0:
            # 1. Задължителни такси и данъци
            local_tax = price_eur * 0.03            # 3% местен данък
            chsi_fees = (price_eur * 0.015) + 150    # ТТРЗЧСИ т.26 + такси
            entry_fee = price_eur * 0.001           # 0.1% АВ

            # 2. Capex прогноза за ремонт
            capex_rate = 150.0 if prop_type == "Жилищен имот" else 50.0
            capex_est = area_sqm * capex_rate

            # 3. Обща себестойност на придобиване (All-In Cost)
            total_acquisition_cost = price_eur + local_tax + chsi_fees + entry_fee + capex_est

            # 4. Прогнозна пазарна стойност след реновиране (ARV - After Repair Value)
            est_market_exit_eur = area_sqm * market_avg_sqm_eur

            # 5. Чиста нетна печалба и Net ROI
            net_profit = round(est_market_exit_eur - total_acquisition_cost, 2)
            net_roi = round((net_profit / total_acquisition_cost) * 100, 1) if total_acquisition_cost > 0 else 0.0

            cursor.execute("""
                UPDATE auctions 
                SET total_acquisition_cost_eur = ?,
                    chsi_fees_eur = ?,
                    local_tax_eur = ?,
                    capex_est_eur = ?,
                    net_profit_eur = ?,
                    net_roi_percent = ?
                WHERE id = ?
            """, (round(total_acquisition_cost, 2), round(chsi_fees, 2), round(local_tax, 2), 
                  round(capex_est, 2), net_profit, net_roi, auc_id))

    conn.commit()
    conn.close()
    print("[✓] Финансовият Net ROI анализ и скритите такси са калкулирани успешно.")

if __name__ == "__main__":
    calculate_net_roi()
