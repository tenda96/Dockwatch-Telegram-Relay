import os
import requests
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
THREAD_ID = os.environ.get("TELEGRAM_THREAD_ID", "").strip()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

@app.route("/mattermost", methods=["POST"])
@app.route("/hooks/<hook_id>", methods=["POST"])
def mattermost(hook_id=None):
    data = request.get_json(silent=True) or {}

    text = (
        data.get("text")
        or data.get("message")
        or str(data)
    )

    username = data.get("username", "Dockwatch")

    if username:
        text = f"**{username}**\n{text}"

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }

    if THREAD_ID:
        payload["message_thread_id"] = THREAD_ID

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, data=payload, timeout=15)

    if not r.ok:
        return jsonify({
            "ok": False,
            "telegram_status": r.status_code,
            "telegram_response": r.text
        }), 500

    return Response("ok", status=200, mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)