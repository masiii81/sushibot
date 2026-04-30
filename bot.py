import requests
import random
import json
import os
import time
from datetime import datetime, timedelta  # ←ここ！！

TOKEN = os.getenv("TOKEN")  # ←後でRenderに設定
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

# ★ 9時と21時にだけ投稿（UTC→日本時間に調整）
def should_run(now_jst, last_run):
    target_hours = [8, 12, 16, 20]
    key = now_jst.strftime("%Y-%m-%d-%H")
    if now_jst.hour in target_hours and key != last_run:
        return True, key
    return False, last_run

while True:
    state = load_state()

    # RenderはUTCなので+9時間でJSTに
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
