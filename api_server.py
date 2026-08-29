import os
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return 'PRO INVEST RADAR OK'

@app.route('/api/deals')
def api_deals():
    return jsonify({'status': 'active'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
