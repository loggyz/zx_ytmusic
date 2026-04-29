import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID"}), 400

    # YT Music specific URL format
    url = f"https://music.youtube.com/watch?v={video_id}"
    
    cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
    
    ydl_opts = {
        'verbose': True,
        'format': 'ba[ext=m4a]/bestaudio/best',
        'nocheckcertificate': True,
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        
        'extractor_args': {
            'youtube': {
                # Music client use karenge kyunki cookies Music ki hain
                'player_client': ['web_music'],
            }
        },
        'http_headers': {
            # Music web client wala User-Agent
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://music.youtube.com/',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "status": "success",
                "url": info.get('url'),
                "title": info.get('title'),
                "artist": info.get('artist')
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
