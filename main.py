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

# Wahi credentials jo Termux pe pass huye
WORKING_PROXIES = [
    "http://purevpn0s8732217:i67s60ep@px460101.pointtoserver.com:10780",
    "http://purevpn0s8732217:i67s60ep@px022505.pointtoserver.com:10780"
]

@app.route("/health")
def health():
    return jsonify({"status": "ok", "mode": "Aggressive Proxy Mode"})

@app.route("/get_track")
def get_track():
    vid = request.args.get("id")
    if not vid: return jsonify({"error": "No ID"}), 400
    
    log.info(f"🚀 Aggressive Extraction: {vid}")
    
    # Is baar hum direct ID use karenge instead of fake URL
    proxies = list(WORKING_PROXIES)
    random.shuffle(proxies)

    for proxy in proxies:
        display_proxy = proxy.split('@')[-1]
        
        ydl_opts = {
            'format': '140/bestaudio',
            'proxy': proxy,
            'quiet': True,
            'nocheckcertificate': True,
            'socket_timeout': 30,
            'geo_bypass': True, # Proxy ki location use karne ke liye
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr', 'web'],
                    'player_skip': ['webpage', 'configs']
                }
            },
            # Masking Render's Identity
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Direct Extraction
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
                stream_url = info.get('url')
                if stream_url:
                    log.info(f"✅ RENDER BYPASS SUCCESS: {display_proxy}")
                    return jsonify({"streamUrl": stream_url, "videoId": vid})
        except Exception as e:
            log.error(f"❌ Render still blocked via {display_proxy}")
            continue

    return jsonify({"error": "YouTube Hard-Blocked Render. Try a different Hosting (like Railway or Vercel)."}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
