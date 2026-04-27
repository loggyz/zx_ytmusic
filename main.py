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

# Wahi credentials jo Termux pe 100% SUCCESS the
WORKING_PROXIES = [
    "http://purevpn0s8732217:i67s60ep@px460101.pointtoserver.com:10780",
    "http://purevpn0s8732217:i67s60ep@px022505.pointtoserver.com:10780"
]

@app.route("/health")
def health():
    return jsonify({"status": "ok", "info": "Last Stand Logic - No Cookies"})

@app.route("/get_track")
def get_track():
    vid = request.args.get("id")
    if not vid: return jsonify({"error": "No ID"}), 400
    
    log.info(f"🔥 Final Attempt for Video: {vid}")
    
    # Randomize Proxies
    proxies = list(WORKING_PROXIES)
    random.shuffle(proxies)

    for proxy in proxies:
        display = proxy.split('@')[-1]
        
        ydl_opts = {
            'format': '140/bestaudio',
            'proxy': proxy,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'socket_timeout': 30,
            # Aggressive Bypass Logic
            'source_address': '0.0.0.0', # Force use of default interface
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_vr', 'ios'], # Termux success mix
                    'player_skip': ['webpage', 'configs']
                }
            },
            # Safari headers usually have lower bot detection
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Format URL exactly like Termux manual command
                test_url = f"https://www.youtube.com/watch?v=7n3z6X5XvWw" 
                # Note: Kuch cases me direct ID dena better hota hai
                info = ydl.extract_info(vid, download=False)
                stream_url = info.get('url')
                if stream_url:
                    log.info(f"✅ RENDER CRACKED: {display}")
                    return jsonify({"streamUrl": stream_url, "videoId": vid})
        except Exception as e:
            log.error(f"💀 Render still hard-blocked on {display}")
            continue

    return jsonify({
        "error": "Render IP Range is Hard-Blocked",
        "suggestion": "Move to Koyeb.com (Free) - It works there!"
    }), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
