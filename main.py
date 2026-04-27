import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Wahi residential proxy jo abhi Termux pe chali
RESIDENTIAL_PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

@app.route("/get_track")
def get_track():
    vid = request.args.get("id")
    if not vid: return jsonify({"error": "No ID"}), 400
    
    log.info(f"🔥 Residential Extraction: {vid}")
    
    # Ekdam simple opts jo tune abhi Termux pe test kiye
    ydl_opts = {
        'format': '140/bestaudio',
        'proxy': RESIDENTIAL_PROXY,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Termux success client
        'extractor_args': {
            'youtube': {
                'player_client': ['android_vr'],
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Jaise Termux ne link diya, waise hi yahan milega
            info = ydl.extract_info(vid, download=False)
            stream_url = info.get('url')
            if stream_url:
                log.info(f"✅ RENDER BYPASS DONE!")
                return jsonify({"streamUrl": stream_url, "videoId": vid})
    except Exception as e:
        log.error(f"❌ Error: {str(e)[:100]}")
        return jsonify({"error": "Proxy Error", "msg": str(e)[:50]}), 502

if __name__ == "__main__":
    # Render port setup
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
