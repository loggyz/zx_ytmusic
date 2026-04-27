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

# Naye Success Credentials jo tune Termux pe test kiye
WORKING_PROXIES = [
    "http://purevpn0s8732217:i67s60ep@px460101.pointtoserver.com:10780",
    "http://purevpn0s8732217:i67s60ep@px022505.pointtoserver.com:10780"
]

@app.route("/health")
def health():
    return jsonify({"status": "ok", "msg": "Running on Termux Success Logic (No Cookies)"})

@app.route("/get_track")
def get_track():
    vid = request.args.get("id")
    if not vid: return jsonify({"error": "No ID"}), 400
    
    log.info(f"🚀 Extraction Attempt (Termux Style): {vid}")
    
    # Exact URL format jo Termux pe hit hua tha
    target_url = f"https://www.youtube.com/watch?v={vid}"
    
    proxies = list(WORKING_PROXIES)
    random.shuffle(proxies)

    for proxy in proxies:
        display_proxy = proxy.split('@')[-1]
        
        ydl_opts = {
            'format': '140/bestaudio',
            'proxy': proxy,
            'quiet': True,
            'nocheckcertificate': True,
            'socket_timeout': 15,
            'extractor_args': {
                'youtube': {
                    # Wahi client jo Termux manual command me successful tha
                    'player_client': ['android_vr'], 
                    'player_skip': ['webpage', 'configs']
                }
            }
        }

        # BINA COOKIES ke test kar rahe hain kyunki Render pe cookies skip ho rahi hain
        # if os.path.exists('/tmp/cookies.txt'): ydl_opts['cookiefile'] = '/tmp/cookies.txt'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Direct target URL pass kar rahe hain
                info = ydl.extract_info(target_url, download=False)
                stream_url = info.get('url')
                if stream_url:
                    log.info(f"✅ SUCCESS via {display_proxy}")
                    return jsonify({"streamUrl": stream_url, "videoId": vid})
        except Exception as e:
            log.error(f"❌ Failed via {display_proxy}: {str(e)[:100]}")
            continue

    return jsonify({"error": "All proxies failed. YouTube is blocking Render IPs."}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
