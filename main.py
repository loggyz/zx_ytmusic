"""
╔══════════════════════════════════════════════════════════════════╗
║  ZEROX HUB — MUSIC ENGINE BACKEND  v5.3                         ║
║  Flask API for Render (Env-based Cookies + Proxy Rotation)       ║
╚══════════════════════════════════════════════════════════════════╝
"""

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

# ─── PROXY VAULT ─────────────────────────────────────────────────
PROXY_LIST = [
    "http://purevpn0s12153504:1LTpwxbCJbEdXo@px022505.pointtoserver.com:10780",
    "http://purevpn0s12153504:1LTpwxbCJbEdXo@px460101.pointtoserver.com:10780",
    "http://g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2@au-per.pvdata.host:8080",
    "http://g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2@ph-man.pvdata.host:8080",
    "http://socialwire:87xb2kziRk4xa@153.121.71.115:822"
]

# ─── COOKIE HANDLER (From Env Var) ───────────────────────────────
COOKIE_PATH = "/tmp/cookies.txt"

def setup_cookies():
    """Environment variable se cookies nikal kar temp file banata hai."""
    # Maan ke chal raha hoon variable ka naam 'COOKIES' rakha hai tune
    cookies_data = os.environ.get("COOKIES") 
    if cookies_data:
        try:
            with open(COOKIE_PATH, "w") as f:
                f.write(cookies_data)
            log.info("🍪 Cookies successfully loaded from Environment Variable")
            return True
        except Exception as e:
            log.error(f"❌ Error writing cookies file: {e}")
    else:
        log.warning("⚠️ No 'COOKIES' environment variable found!")
    return False

# Initialize cookies at startup
HAS_COOKIES = setup_cookies()

# ══════════════════════════════════════════════════════════════════
#  EXTRACTION ENGINE
# ══════════════════════════════════════════════════════════════════

def extract_m4a(video_id: str):
    log.info(f"[stream] 🔄 Extraction start: {video_id}")
    video_id = video_id.strip()[:11]
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    shuffled_proxies = list(PROXY_LIST)
    random.shuffle(shuffled_proxies)

    for proxy in shuffled_proxies:
        safe_log = proxy.split('@')[-1]
        
        ydl_opts = {
            'format': '140/bestaudio',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'proxy': proxy,
            'socket_timeout': 12,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios'],
                    'skip': ['webpage', 'configs']
                }
            }
        }
        
        # Agar cookies env se mil gayi thin, toh use karo
        if os.path.exists(COOKIE_PATH):
            ydl_opts['cookiefile'] = COOKIE_PATH

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info.get('url')
                if stream_url:
                    log.info(f"✅ Success via {safe_log}")
                    return stream_url
        except Exception as e:
            log.warning(f"⚠️ Proxy failed ({safe_log}): {str(e)[:50]}")
            continue
            
    return None

# ══════════════════════════════════════════════════════════════════
#  ROUTES (Full 500+ lines logic simplified for main file)
# ══════════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "node": os.environ.get("NODE_VERSION", "Missing"),
        "cookies_env": "Found" if os.environ.get("COOKIES") else "Missing",
        "cookies_file": os.path.exists(COOKIE_PATH)
    }), 200

@app.route('/get_track')
def get_track():
    vid = request.args.get('id')
    if not vid: return jsonify({"error": "No ID"}), 400
    url = extract_m4a(vid)
    if url: return jsonify({"streamUrl": url, "videoId": vid})
    return jsonify({"error": "Extraction failed"}), 502

# [Yahan apne purane main2.py ke baki functions: search, normal, vibe merge kar lena]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
