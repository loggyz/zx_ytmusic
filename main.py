import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Logging setup taaki Render logs mein dikhe kya ho rha hai
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Tera Owl Proxy (Residential)
RESIDENTIAL_PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

@app.route("/")
def home():
    return "YouTube Bypass Server is Live!", 200

@app.route("/get_track")
def get_track():
    video_id = request.args.get("id")
    if not video_id:
        return jsonify({"error": "Missing video id"}), 400

    log.info(f"🚀 Processing ID: {video_id} via Redirector Bypass")

    # Wahi "Jadu" wala URL jo tune Termux pe test kiya
    # Isse YouTube ki main API bypass ho jati hai
    bypass_url = f"http://googleusercontent.com/youtube.com/{video_id}"

    ydl_opts = {
        'format': '140/bestaudio',
        'proxy': RESIDENTIAL_PROXY,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android_vr'],
                'player_skip': ['webpage', 'configs'],
            }
        },
        # Real headers taaki bot detection aur kam ho jaye
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Hum ID ki jagah poora bypass_url pass kar rahe hain
            info = ydl.extract_info(bypass_url, download=False)
            stream_url = info.get('url')
            
            if stream_url:
                log.info("✅ Success: Link generated!")
                return jsonify({
                    "streamUrl": stream_url,
                    "videoId": video_id,
                    "method": "redirector_bypass"
                })
            else:
                return jsonify({"error": "No stream URL found"}), 500

    except Exception as e:
        log.error(f"❌ Extraction Failed: {str(e)}")
        return jsonify({
            "error": "Extraction Failed",
            "details": str(e)[:100]
        }), 502

if __name__ == "__main__":
    # Render default port 10000 use karta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
