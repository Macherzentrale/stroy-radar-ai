from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "<h1 style='color:cyan; font-family:sans-serif; text-align:center; margin-top:50px;'>PRO INVEST RADAR AI .BG – ONLINE</h1>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
