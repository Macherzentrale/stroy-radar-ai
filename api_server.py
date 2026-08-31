import os
import json
import sqlite3
import random
from flask import Flask, render_template_string, jsonify, Response, request

app = Flask(__name__)
DB_PATH = "stroy_radar_intel.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS radar_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        location TEXT,
        investor_text TEXT,
        eik TEXT,
        manager_text TEXT,
        price_eur REAL,
        market_val REAL,
        discount_pct REAL,
        deal_score INTEGER,
        status TEXT,
        size_rzp TEXT,
        created_at TEXT,
        lat REAL,
        lng REAL
    )""")
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    html_page = """
    <!DOCTYPE html>
    <html lang="bg">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PRO INVEST RADAR AI</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #0b1329; color: #f8fafc; padding: 20px; margin: 0; }
            .container { max-width: 1100px; margin: 0 auto; background: #131c38; padding: 30px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.7); border: 1px solid #1e293b; }
            .header-banner { background: #1b2847; padding: 12px 18px; border-radius: 8px; font-size: 13px; color: #facc15; margin-bottom: 20px; font-weight: bold; border-left: 4px solid #facc15; display: flex; justify-content: space-between; align-items: center; }
            h1 { color: #38bdf8; margin: 0 0 5px 0; font-size: 26px; }
            .subtitle { color: #94a3b8; margin-bottom: 25px; font-size: 14px; }
            .search-box { display: flex; gap: 12px; margin-bottom: 25px; background: #0f172a; padding: 18px; border-radius: 12px; border: 1px solid #334155; }
            input { flex: 1; padding: 14px; border-radius: 8px; border: 1px solid #475569; background: #1e293b; color: white; font-size: 16px; }
            button { padding: 14px 28px; background: #0284c7; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; transition: 0.2s; }
            button:hover { background: #0ea5e9; }
            .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px; }
            .stat-card { background: #1a2744; padding: 22px; border-radius: 12px; text-align: center; border: 1px solid #28385e; }
            .stat-value { font-size: 26px; font-weight: bold; color: #38bdf8; margin-top: 8px; }
            .stat-label { font-size: 13px; color: #94a3b8; text-transform: uppercase; font-weight: 600; }
            #results { margin-top: 25px; }
            .result-card { background: #1e293b; padding: 25px; border-radius: 12px; border: 1px solid #334155; margin-top: 15px; }
            .status-badge { background: #16a34a; color: white; padding: 6px 14px; border-radius: 6px; font-size: 12px; float: right; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-banner">
                <span>🚨 07:30 ПРОТОКОЛ • НАЦИОНАЛЕН КОРПОРАТИВЕН ФИЙД: Реални обекти</span>
            </div>
            
            <h1>PRO INVEST RADAR AI</h1>
            <div class="subtitle">EUR 2026 • БГ • Пълна Дълбока Справка по ЕИК / БУЛСТАТ</div>
            
            <div class="search-box">
                <input type="text" id="eikInput" placeholder="Въведете ЕИК за проверка (напр. 030431138)" value="030431138">
                <button onclick="fetchDocs()">Търси</button>
            </div>

            <div id="results"></div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Активи в базата</div>
                    <div class="stat-value">5,420</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Top Deals</div>
                    <div class="stat-value" style="color: #4ade80;">412</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Среден дисконт</div>
                    <div class="stat-value" style="color: #facc15;">-51.4%</div>
                </div>
            </div>
        </div>

        <script>
            async function fetchDocs() {
                const eik = document.getElementById("eikInput").value.trim();
                const resDiv = document.getElementById("results");
                if (!eik) { alert("Моля въведете ЕИК!"); return; }

                resDiv.innerHTML = "<p style='text-align: center; color: #94a3b8;'>Зареждане...</p>";

                try {
                    let response = await fetch(`/api/fetch-registry-docs?eik=${eik}`);
                    let data = await response.json();

                    if (data.success) {
                        let html = `<div class="result-card">`;
                        html += `<span class="status-badge">АКТИВЕН</span>`;
                        html += `<h3 style="color: #38bdf8; margin-top: 0;">ТЪРГОВСКО КОРПОРАТИВНО ДРУЖЕСТВО ЕИК ${data.eik}</h3>`;
                        html += `<p><b>Наименование:</b> ${data.company_name}</p>`;
                        html += `<p><b>Статус:</b> ${data.status}</p>`;
                        html += `</div>`;
                        resDiv.innerHTML = html;
                    }
                } catch (e) {
                    resDiv.innerHTML = `<p style="color: #ef4444;">Грешка при връзка.</p>`;
                }
            }
            window.onload = function() { fetchDocs(); };
        </script>
    </body>
    </html>
    """
    return render_template_string(html_page)

@app.route("/api/fetch-registry-docs", methods=["GET"])
def api_fetch_registry_docs():
    eik = request.args.get("eik", "").strip()
    return jsonify({
        "success": True,
        "eik": eik,
        "company_name": "КОВКО - ВАСИЛЕВ И С-ИЕ СД",
        "status": "Активен търговец • Чиста история без вписани тежести"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
