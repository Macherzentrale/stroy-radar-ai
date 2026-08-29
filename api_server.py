from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import sqlite3
import urllib.parse
import os

DB_NAME = "stroy_radar_intel.db"

class CustomAppServer(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # 1. API Endpoint за данните
        if path.startswith("/api"):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            query = "SELECT title, city, property_type, area_sqm, price_bgn, price_eur, price_sqm_eur, market_avg_sqm_eur, discount_percentage, est_gross_profit_eur, deadline, source_url, ai_score, ai_rating, risk_flags, ai_verdict FROM auctions ORDER BY ai_score DESC"
            try:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()
                conn.close()

                results = [{
                    "title": r[0], "city": r[1], "property_type": r[2], "area_sqm": r[3],
                    "price_bgn": r[4], "price_eur": r[5], "price_sqm_eur": r[6],
                    "market_avg_sqm_eur": r[7], "discount_percentage": r[8],
                    "est_gross_profit_eur": r[9], "deadline": r[10], "source_url": r[11],
                    "ai_score": r[12], "ai_rating": r[13], "risk_flags": r[14], "ai_verdict": r[15]
                } for r in rows]

                resp = {"status": "success", "count": len(results), "data": results}
                self.wfile.write(json.dumps(resp, ensure_ascii=False, indent=2).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        # 2. Зареждане на вашия оригинален HTML файл за началната страница
        if path == "/" or path == "":
            for candidate in ["index.html", "stroy_radar.html", "dashboard.html", "app.html"]:
                if os.path.exists(candidate):
                    self.path = f"/{candidate}"
                    break

        return super().do_GET()

def run_server(port=8080):
    server = HTTPServer(('', port), CustomAppServer)
    print(f"[*] Сървърът сервира оригиналния фронтенд на порт {port}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
