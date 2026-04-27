import os
import random
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# SUCCESS CREDENTIALS
WORKING_PROXIES = [
    "http://purevpn0s8732217:i67s60ep@px460101.pointtoserver.com:10780",
    "http://purevpn0s8732217:i67s60ep@px022505.pointtoserver.com:10780"
]

COOKIE_PATH = "/tmp/cookies.txt"

def setup_cookies():
    raw = os.environ.get("COOKIES")
    if raw:
        with open(COOKIE_PATH, "w") as f:
            f.write(raw)
        return True
    return False

setup_cookies()

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "cookies_ready": os.path.exists(COOKIE_PATH),
        "proxies_count": len(WORKING_PROXIES)
    })

@app.route("/get_track")
def get_track():
    vid = request.args.get("id", "7n3z6X5XvWw")
    log.info(f"🚀 Testing Extraction for: {vid}")
    
    # Exact Termux Logic
    proxies = list(WORKING_PROXIES)
    random.shuffle(proxies)

    for proxy in proxies:
        display_proxy = proxy.split('@')[-1]
        log.info(f"Trying Proxy: {display_proxy}")
        
        ydl_opts = {
            'format': '140/bestaudio',
            'proxy': proxy,
            'quiet': False, # Logs dekhne ke liye True ki jagah False
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr'],
                    'player_skip': ['webpage', 'configs']
                }
            }
        }

        if os.path.exists(COOKIE_PATH):
            ydl_opts['cookiefile'] = COOKIE_PATH

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Termux success: direct ID passing
                info = ydl.extract_info(vid, download=False)
                stream_url = info.get('url')
                if stream_url:
                    log.info(f"✅ SUCCESS via {display_proxy}")
                    return jsonify({"streamUrl": stream_url, "proxy": display_proxy})
        except Exception as e:
            log.error(f"❌ Failed via {display_proxy}: {str(e)[:100]}")
            continue

    return jsonify({"error": "All proxies failed", "logs": "Check Render Dashboard"}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
