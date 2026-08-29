import os
from flask import Flask, render_template_string
app = Flask(__name__)

@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html lang="bg">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PRO INVEST RADAR .BG</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body style="background:#080d19; color:#fff; font-family:sans-serif; text-align:center; padding-top:50px;">
        <div class="container" style="max-width:600px; background:#0d1527; padding:30px; border-radius:15px; border:1px solid #19253d;">
            <h2 style="color:#00f0ff; font-weight:bold;">PRO INVEST RADAR AI .BG</h2>
            <p class="text-secondary mt-3">Институционалният радар работи успешно в реално време.</p>
            <hr style="border-color:#334155;">
            <a href="https://t.me/stroyradar_support" target="_blank" class="btn btn-info fw-bold w-150 py-2">Telegram Поддръжка</a>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
