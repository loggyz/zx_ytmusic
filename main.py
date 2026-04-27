import os
import re
import time
import random
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp
from ytmusicapi import YTMusic

app = Flask(__name__)
CORS(app, origins="*")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
yt = YTMusic()

# ─── WORKING CONFIG ──────────────────────────────────────────────
WORKING_PROXIES = [
    "http://purevpn0s8732217:i67s60ep@px460101.pointtoserver.com:10780",
    "http://purevpn0s8732217:i67s60ep@px022505.pointtoserver.com:10780"
]

COOKIE_PATH = "/tmp/cookies.txt"

def setup_cookies():
    raw = os.environ.get("COOKIES")
    if raw:
        try:
            with open(COOKIE_PATH, "w") as f: f.write(raw)
            return True
        except: return False
    return False

setup_cookies()

# ─── UTILS ───────────────────────────────────────────────────────
def clean_name(text):
    if not text: return ""
    text = re.sub(r"\[.*?\]|\(.*?\)|\b(official|audio|video|lyrics|4k|hd)\b", " ", text, flags=re.I)
    return re.sub(r"\s{2,}", " ", text).strip()

def fmt_track(t):
    arts = t.get("artists") or [{"name": "Unknown"}]
    return {
        "title": clean_name(t.get("title", "")),
        "artist": clean_name(arts[0].get("name", "Unknown")),
        "artistId": arts[0].get("browseId"),
        "videoId": t.get("videoId", ""),
        "thumbnail": t.get("thumbnails", [{}])[-1].get("url"),
        "duration": t.get("duration", ""),
    }

# ─── EXTRACTION ENGINE (Based on your Success Test) ──────────────
def extract_m4a(video_id):
    log.info(f"[stream] 🔄 Fetching: {video_id}")
    # Termux success logic URL
    target_url = f"https://www.youtube.com/watch?v={video_id}"
    
    proxies = list(WORKING_PROXIES)
    random.shuffle(proxies)

    for proxy in proxies:
        ydl_opts = {
            'format': '140/bestaudio',
            'proxy': proxy,
            'quiet': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr'], # Critical success factor
                    'skip': ['webpage', 'configs']
                }
            }
        }
        
        if os.path.exists(COOKIE_PATH):
            ydl_opts['cookiefile'] = COOKIE_PATH

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(target_url, download=False)
                return info.get('url')
        except Exception as e:
            log.warning(f"⚠️ Proxy failed: {str(e)[:50]}")
            continue
    return None

# ─── ROUTES ──────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "cookies": os.path.exists(COOKIE_PATH), "node": os.environ.get("NODE_VERSION")})

@app.route('/get_track')
def get_track():
    vid = request.args.get('id')
    url = extract_m4a(vid)
    return jsonify({"streamUrl": url, "videoId": vid}) if url else (jsonify({"error": "Failed"}), 502)

@app.route("/search")
def search():
    q = request.args.get("q", "")
    res = yt.search(q, filter="songs")
    return jsonify({"results": [fmt_track(t) for t in res[:10]]})

# [Yahan normal aur vibe routes add kar lena jo main2.py me the]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
