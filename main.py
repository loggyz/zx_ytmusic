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

# ─── PROXY LIST ──────────────────────────────────────────────────
PROXY_LIST = [
    "http://purevpn0s12153504:1LTpwxbCJbEdXo@px022505.pointtoserver.com:10780",
    "http://purevpn0s12153504:1LTpwxbCJbEdXo@px460101.pointtoserver.com:10780",
    "http://g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2@au-per.pvdata.host:8080",
    "http://g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2@ph-man.pvdata.host:8080",
    "http://socialwire:87xb2kziRk4xa@153.121.71.115:822"
]

def clean_name(text):
    if not text: return ""
    return re.sub(r"\[.*?\]|\(.*?\)", "", text).strip()

def extract_m4a(video_id):
    log.info(f"[stream] 🔄 Request for: {video_id}")
    video_id = video_id.strip()[:11]
    
    # Shuffle proxies
    random.shuffle(PROXY_LIST)
    
    for proxy in PROXY_LIST:
        safe_log = proxy.split('@')[-1]
        log.info(f"🚀 Trying Proxy: {safe_log}")
        
        ydl_opts = {
            'format': '140/bestaudio',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'proxy': proxy,
            'source_address': '0.0.0.0',
            'socket_timeout': 10,
            # 'external_downloader': 'aria2c', # Render pe aria2 nahi hota toh ise rehne do
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios'], # Mobile clients are less restricted
                    'player_skip': ['webpage', 'configs']
                }
            }
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Direct link logic
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                stream_url = info.get('url')
                if stream_url:
                    log.info(f"✅ SUCCESS via {safe_log}")
                    return stream_url
        except Exception as e:
            log.warning(f"⚠️ Failed with {safe_log}: {str(e)[:50]}")
            continue
            
    return None

# Saare Endpoints (Same as your v5.0)
@app.route("/health")
def health(): return jsonify({"status": "ok", "engine": "ZeroX Proxy Edition"}), 200

@app.route('/get_track')
def get_track():
    vid = request.args.get('id')
    url = extract_m4a(vid)
    if url: return jsonify({"streamUrl": url, "videoId": vid})
    return jsonify({"error": "All proxies failed"}), 502

# Baki search aur normal routes wahi rakho...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
