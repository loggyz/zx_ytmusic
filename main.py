import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Tera naya Residential Proxy (Owl Proxy)
RESIDENTIAL_PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

@app.route("/get_track")
def get_track():
    vid = request.args.get("id")
    if not vid: return jsonify({"error": "No ID"}), 400
    
    log.info(f"🚀 Using Residential Proxy (Comcast) for: {vid}")
    
    ydl_opts = {
        'format': '140/bestaudio',
        'proxy': RESIDENTIAL_PROXY,
        'quiet': True,
        'nocheckcertificate': True,
        'socket_timeout': 30,
        'extractor_args': {
            'youtube': {
                # Residential IP ke saath ye clients makkhan chalte hain
                'player_client': ['android', 'web'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        # Real Browser Headers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Note: Direct video URL format
            info = ydl.extract_info(vid, download=False)
            stream_url = info.get('url')
            if stream_url:
                log.info(f"✅ SUCCESS: Residential Bypass Worked!")
                return jsonify({
                    "streamUrl": stream_url, 
                    "videoId": vid,
                    "provider": "Comcast-Residential"
                })
    except Exception as e:
        log.error(f"❌ Failed even with Comcast: {str(e)[:100]}")
        return jsonify({"error": "Proxy connection issue", "details": str(e)[:50]}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
