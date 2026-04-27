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
        return jsonify({"error": "ID missing"}), 400

    target_url = f"https://www.youtube.com/watch?v={video_id}"
    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"
    
    ydl_opts = {
        'proxy': proxy_url,
        'quiet': False, # Logs zaroori hain authentication ke liye
        'no_warnings': False,
        'format': 'bestaudio/best',
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        # OAuth enable kar rahe hain taaki PoToken ki zaroorat na pade
        'username': 'oauth2',
        'password': '',
        'extractor_args': {
            'youtube': {
                'player_client': ['tv'], # TV client sabse stable hai residential proxy par
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            stream_url = info.get('url')
            
            if stream_url:
                return jsonify({"status": "success", "stream_url": stream_url})
            else:
                return jsonify({"status": "error", "message": "Stream not found"}), 500
                
    except Exception as e:
        # Agar code maange toh logs mein dikhega
        print(f"DEBUG ERROR: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
