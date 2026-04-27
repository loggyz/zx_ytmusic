import yt_dlp
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/get_stream')
def get_stream():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "ID de!"}), 400

    # Direct YouTube Link (Back to basics)
    target_url = f"https://www.youtube.com/watch?v={video_id}"
    
    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"
    cookie_path = 'cookies.txt'

    ydl_opts = {
        'proxy': proxy_url,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'format': 'bestaudio/best',
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        # Yeh hai asli game changer: YouTube ko Android App dikhana
        'extractor_args': {
            'youtube': {
                'player_client': ['android'],
                'skip': ['webpage', 'authcheck']
            }
        },
        'user_agent': 'com.google.android.youtube/19.08.35 (Linux; U; Android 11; en_US; Pixel 4 XL; Build/RP1A.200720.009)',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Check if cookie exists for debugging
            has_cookies = os.path.exists(cookie_path)
            
            info = ydl.extract_info(target_url, download=False)
            stream_url = info.get('url')
            
            if stream_url:
                return jsonify({
                    "status": "success",
                    "cookies_loaded": has_cookies,
                    "stream_url": stream_url
                })
            else:
                return jsonify({"status": "error", "message": "Link fail ho gaya"}), 500
                
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": str(e),
            "cookies_found": os.path.exists(cookie_path)
        }), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
