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
        try:
            with open(COOKIE_PATH, "w") as f:
                f.write(raw)
            return True
        except:
            return False
    return False

setup_cookies()

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "cookies": os.path.exists(COOKIE_PATH),
        "node": os.environ.get("NODE_VERSION")
    })

@app.route("/get_track")
def get_track():
    vid = request.args.get("id")
    if not vid: return jsonify({"error": "No ID"}), 400
    
    log.info(f"🚀 Extraction Attempt via WEB client: {vid}")
    
    proxies = list(WORKING_PROXIES)
    random.shuffle(proxies)

    for proxy in proxies:
        display_proxy = proxy.split('@')[-1]
        
        ydl_opts = {
            'format': '140/bestaudio',
            'proxy': proxy,
            'quiet': True,
            'nocheckcertificate': True,
            'socket_timeout': 20,
            'extractor_args': {
                'youtube': {
                    # WEB client cookies ke liye sabse stable hai
                    'player_client': ['web'],
                    'player_skip': ['configs', 'webpage']
                }
            },
            # Real browser headers
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://www.youtube.com',
                'Referer': 'https://www.youtube.com/'
            }
        }

        if os.path.exists(COOKIE_PATH):
            ydl_opts['cookiefile'] = COOKIE_PATH

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Target URL format change
                target = f"https://www.youtube.com/watch?v={vid}"
                info = ydl.extract_info(target, download=False)
                stream_url = info.get('url')
                if stream_url:
                    log.info(f"✅ SUCCESS via WEB client & {display_proxy}")
                    return jsonify({"streamUrl": stream_url, "videoId": vid})
        except Exception as e:
            log.error(f"❌ Failed via {display_proxy}: {str(e)[:100]}")
            continue

    return jsonify({"error": "Bypass failed. Try updating cookies."}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
