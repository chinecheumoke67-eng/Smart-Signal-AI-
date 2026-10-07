import os
import requests
from flask import Flask, request

app = Flask(__name__)


TOKEN = os.environ.get("BOT_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

@app.route("/", methods=["GET"])
def home():
    return "Smart Signal AI is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    message = data.get("message", {})
    chat = message.get("chat", {})
    text = message.get("text", "")

    if not chat:
        return "ok"

    chat_id = chat.get("id")

    if text == "/start":
        reply = (
            "🤖 Welcome to Smart Signal AI!\n\n"
            "📊 Type /signal to request a signal."
        )

    elif text == "/signal":
        reply = (
            "📊 SMART SIGNAL AI\n\n"
            "💱 EUR/USD\n"
            "⏱ Timeframe: 1 Minute\n\n"
            "🟢 UP / CALL\n"
            "📈 EMA + RSI analysis\n\n"
            "⚠️ This is an informational signal, "
            "not a guarantee of profit."
        )

    else:
        reply = "Type /signal to request a signal."

    requests.post(
        f"{API}/sendMessage",
        json={"chat_id": chat_id, "text": reply},
        timeout=10
    )

    return "ok"

if name == "main":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
