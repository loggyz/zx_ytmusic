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

    # Normal YouTube URL use karenge kyunki cookies ke saath ye sabse best chalta hai
    target_url = f"https://www.youtube.com/watch?v={video_id}"
    
    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

    # Cookies file ka path check karo
    cookie_path = 'cookies.txt'
    
    ydl_opts = {
        'proxy': proxy_url,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'format': 'bestaudio/best',
        # Cookies load karne ki command
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            stream_url = info.get('url')
            
            if stream_url:
                return jsonify({"status": "success", "stream_url": stream_url})
            else:
                return jsonify({"status": "error", "message": "Link fail ho gaya"}), 500
                
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
