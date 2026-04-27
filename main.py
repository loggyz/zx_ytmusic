import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Wahi residential proxy jo Termux pe link de rahi hai
RESIDENTIAL_PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

@app.route("/get_track")
def get_track():
    vid = request.args.get("id")
    if not vid: return jsonify({"error": "No ID"}), 400
    
    log.info(f"🚀 Fetching for ID: {vid}")
    
    # Ekdam wahi settings jo Termux pe link nikaal rahi hain
    ydl_opts = {
        'format': '140/bestaudio', # Direct audio format as per your success
        'proxy': RESIDENTIAL_PROXY,
        'quiet': True,
        'nocheckcertificate': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android_vr'], # Termux success client
                'player_skip': ['webpage', 'configs'],
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Hum wahi video ID use karenge jo Termux pe chali
            # Agar id '1' aa rahi hai toh wo use '7n3z6X5XvWw' mein convert kar deta hai automatically
            info = ydl.extract_info(vid, download=False)
            stream_url = info.get('url')
            
            if stream_url:
                log.info(f"✅ LINK GENERATED ON RENDER!")
                return jsonify({
                    "streamUrl": stream_url, 
                    "videoId": vid
                })
    except Exception as e:
        log.error(f"❌ Render Error: {str(e)[:100]}")
        return jsonify({"error": "Extraction Failed", "details": str(e)[:50]}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
