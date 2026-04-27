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

# SUCCESS CREDENTIALS (Updated)
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

# Initialize cookies
setup_cookies()

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "cookies_ready": os.path.exists(COOKIE_PATH),
        "node_version": os.environ.get("NODE_VERSION", "Not Set")
    })

@app.route("/get_track")
def get_track():
    vid = request.args.get("id")
    if not vid:
        return jsonify({"error": "No ID provided"}), 400
        
    log.info(f"🚀 Extraction Attempt for: {vid}")
    
    proxies = list(WORKING_PROXIES)
    random.shuffle(proxies)

    for proxy in proxies:
        display_proxy = proxy.split('@')[-1]
        
        # Updated Options: Removing android_vr because it hates cookies
        ydl_opts = {
            'format': '140/bestaudio',
            'proxy': proxy,
            'quiet': True,
            'nocheckcertificate': True,
            'socket_timeout': 15,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios'], # Better for cookie support
                    'player_skip': ['webpage', 'configs']
                }
            },
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'
        }

        if os.path.exists(COOKIE_PATH):
            ydl_opts['cookiefile'] = COOKIE_PATH

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Direct ID extraction
                info = ydl.extract_info(vid, download=False)
                stream_url = info.get('url')
                if stream_url:
                    log.info(f"✅ SUCCESS via {display_proxy}")
                    return jsonify({"streamUrl": stream_url, "videoId": vid})
        except Exception as e:
            log.error(f"❌ Failed via {display_proxy}: {str(e)[:100]}")
            continue

    return jsonify({"error": "All proxies failed. Check cookies or IP status."}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
