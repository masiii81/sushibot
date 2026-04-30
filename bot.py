import requests
import random
import json
import os
import time
from datetime import datetime, timedelta
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = os.getenv("TOKEN")
URL = os.getenv("MISSKEY_URL", "https://misskey.io/api/notes/create")
STATE_FILE = "state.json"

normal_lines = [
    "ｽｼｽｼ…","ｽﾒｰｼｰ","ｼｬﾘ!ｼｬﾘ!","ｵﾚｽｼ...",
    "ｽｼｰｽｼｰ","ﾇﾇ?ｽｼｰ","ｵｽｰｼｰ","ｼｰｽｰ!!",
    "ﾇｼﾇｼｰ","ﾇｼﾇｼｰ"
]
noises = [
    "ｷﾞｶﾞｷﾞｶﾞﾌﾝﾌﾝwｶﾞｶﾞｶﾞｶﾞｶﾞw",
    "ぱるぱるぅ!!",
    "モエルーワ！",
    "ディグダ、ダァーッ!!"
]

noise_rate = 0.01
nushi_to_ore = 0.25
ore_to_final = 0.15

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last": None, "last_run": ""}

def save_state(s):
    with open(STATE_FILE, "w") as f:
        json.dump(s, f)

def generate_text(last):
    if last == "ﾇｼﾇｼｰ" and random.random() < nushi_to_ore:
        return "ｵﾚﾇｼｰ!!"
    if last == "ｵﾚﾇｼｰ!!" and random.random() < ore_to_final:
        return "ｵ...ｵ...ｵﾚﾓﾇｼｰ!!"

    base = random.choice(normal_lines)
    if random.random() < noise_rate:
        return random.choice(noises) if random.random()<0.5 else base+" "+random.choice(noises)
    return base

def avoid_repeat(new_text, last_text):
    for _ in range(5):
        if new_text != last_text:
            return new_text
        new_text = generate_text(last_text)
    return new_text

def post(text):
    requests.post(URL, json={"i": TOKEN, "text": text})

def should_run(now_jst, last_run):
    target_hours = [8, 12, 16, 20]
    key = now_jst.strftime("%Y-%m-%d-%H")
    if now_jst.hour in target_hours and key != last_run:
        return True, key
    return False, last_run

# ===== bot処理 =====
def run_bot():
    while True:
        state = load_state()

        now = datetime.utcnow()
        now_jst = now + timedelta(hours=9)

        run, key = should_run(now_jst, state.get("last_run",""))
        if run:
            text = generate_text(state.get("last"))
            text = avoid_repeat(text, state.get("last"))
            post(text)
            state["last"] = text
            state["last_run"] = key
            save_state(state)
            print("posted:", text)

        time.sleep(60)

# ===== ダミーサーバー =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

# ===== 起動 =====
threading.Thread(target=run_bot, daemon=True).start()
run_server()
