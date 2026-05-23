import os
import re
import requests
from datetime import datetime
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
THREAD_ID = os.environ.get("TELEGRAM_THREAD_ID", "").strip()

def log(message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {message}", flush=True)

def clean_markdown(text):
    text = text.strip()
    text = text.replace("#####", "")
    text = text.replace("####", "")
    text = text.replace("###", "")
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace("_", "")
    text = text.replace("`", "")
    return text.strip()

def split_items(value):
    value = value.strip()
    value = value.replace("<br>", "\n")
    value = value.replace("<br/>", "\n")
    value = value.replace("<br />", "\n")

    parts = []
    for chunk in re.split(r",|\n", value):
        chunk = clean_markdown(chunk)
        chunk = chunk.strip(" |")
        if chunk:
            parts.append(chunk)

    return parts

def title_emoji(title):
    t = title.lower()

    if "test" in t:
        return "🧪"
    if "state" in t or "container" in t:
        return "📦"
    if "update" in t:
        return "🔄"
    if "pruned" in t or "prune" in t:
        return "🧹"
    if "health" in t:
        return "🩺"
    if "usage" in t:
        return "⚠️"
    if "security" in t or "vulnerab" in t:
        return "🛡️"

    return "🐳"

def section_emoji(section):
    s = section.lower()

    if "added" in s:
        return "✅"
    if "removed" in s:
        return "🗑️"
    if "changed" in s:
        return "🔁"
    if "available" in s:
        return "📦"
    if "updated" in s:
        return "⬆️"
    if "networks" in s:
        return "🌐"
    if "volumes" in s:
        return "💾"
    if "images" in s or "image" in s:
        return "🖼️"
    if "memory" in s:
        return "🧠"
    if "cpu" in s:
        return "⚙️"
    if "critical" in s:
        return "🚨"
    if "high" in s:
        return "🔴"
    if "medium" in s:
        return "🟠"
    if "low" in s:
        return "🟡"

    return "•"

def is_table_noise(line):
    line = line.strip()
    compact = line.replace(" ", "").lower()

    if compact in ["|type|container|", "|type|pruned|"]:
        return True

    if compact.startswith("|") and compact.endswith("|"):
        inner = compact.strip("|")
        if inner and all(c in "-:|" for c in inner):
            return True

    return False


def parse_table_line(line):
    line = line.strip()

    if not line.startswith("|") or not line.endswith("|"):
        return None

    cells = [clean_markdown(c) for c in line.strip("|").split("|")]

    if len(cells) < 2:
        return None

    left = cells[0].strip()
    right = " | ".join(cells[1:]).strip()

    if not left or not right:
        return None

    if left.lower() == "type":
        return None

    if "---" in left or "---" in right:
        return None

    return left, right

def format_item(section, item):
    m = re.match(r"^(.+?)\s+\[(.+?)\s*(?:→|->)\s*(.+?)\]$", item)

    if m and section.lower() in ["updated", "changed"]:
        name = m.group(1).strip()
        old = m.group(2).strip()
        new = m.group(3).strip()
        return f"• {name}: {old} → {new}"

    return f"• {item}"

def format_dockwatch_message(text):
    original = text.strip()

    if not original:
        return ""

    lines = original.splitlines()

    title = None
    server = None
    normal_lines = []
    table_sections = []

    for line in lines:
        raw = line.strip()

        if not raw:
            continue

        if is_table_noise(raw):
            continue

        if raw.startswith("#####"):
            title = clean_markdown(raw)
            continue

        if raw.lower().startswith("server:"):
            server = clean_markdown(raw.replace("Server:", "", 1))
            continue

        table = parse_table_line(raw)
        if table:
            table_sections.append(table)
            continue

        cleaned = clean_markdown(raw)

        if cleaned:
            if cleaned.startswith("- "):
                cleaned = "• " + cleaned[2:]
            normal_lines.append(cleaned)

    if not title:
        title = "Dockwatch notification"

    title = title.replace("Dockwatch:", "Dockwatch —")
    output = [f"{title_emoji(title)} {title}"]

    if server:
        output.append(f"Server: {server}")

    if table_sections:
        output.append("")

        for section, value in table_sections:
            items = split_items(value)
            if not items:
                continue

            output.append(f"{section_emoji(section)} {section}:")

            for item in items:
                output.append(format_item(section, item))

            output.append("")

    if normal_lines:
        output.append("")

        for line in normal_lines:
            output.append(line)

    formatted = "\n".join(output).strip()

    return formatted or original

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "chat_id": CHAT_ID,
        "thread_id": THREAD_ID or None,
    })

@app.route("/mattermost", methods=["POST"])
@app.route("/hooks/<hook_id>", methods=["POST"])
def mattermost(hook_id=None):
    data = request.get_json(silent=True) or {}

    username = data.get("username", "Dockwatch")
    raw_text = (data.get("text") or data.get("message") or "").strip()
    text = format_dockwatch_message(raw_text)

    log("Incoming webhook received")
    log(f"hook_id={hook_id}")
    log(f"username={username!r}")
    log(f"raw_text_length={len(raw_text)}")
    log(f"formatted_text_length={len(text)}")
    log(f"text_preview={text.replace(chr(10), ' ')[:250]!r}")
    log(f"telegram_chat_id={CHAT_ID}")
    log(f"telegram_thread_id={THREAD_ID or 'none'}")

    if not text:
        log("Empty Dockwatch message, skipping Telegram send")
        return Response("ok", status=200, mimetype="text/plain")

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }

    if THREAD_ID:
        payload["message_thread_id"] = THREAD_ID

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    try:
        r = requests.post(url, data=payload, timeout=15)
    except Exception as e:
        log(f"Telegram request exception: {repr(e)}")
        return jsonify({
            "ok": False,
            "error": repr(e),
        }), 500

    log(f"telegram_status={r.status_code}")
    log(f"telegram_response={r.text[:1000]}")

    if not r.ok:
        return jsonify({
            "ok": False,
            "telegram_status": r.status_code,
            "telegram_response": r.text,
        }), 500

    return Response("ok", status=200, mimetype="text/plain")

if __name__ == "__main__":
    log("Starting Dockwatch Telegram Relay")
    log(f"Configured chat_id={CHAT_ID}")
    log(f"Configured thread_id={THREAD_ID or 'none'}")
    app.run(host="0.0.0.0", port=8080)
