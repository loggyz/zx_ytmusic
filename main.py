import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID"}), 400

    # Clean URL logic
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        
        # DOCUMENTATION FIX: Use bgutilhttp for the server option
        'extractor_args': {
            'youtubepot-bgutilhttp': {
                'base_url': 'http://127.0.0.1:4416' 
            }
        },
        
        # Add a real browser user agent as per PO Token Guide
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        
        # Remote scripts are still required for the 'jsc' (JS Challenge)
        'compat_opts': {'remote-components': 'ejs:github'},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info and 'url' in info:
                return jsonify({
                    "status": "success",
                    "url": info['url'],
                    "title": info.get('title')
                })
            
            return jsonify({"status": "error", "message": "Could not extract URL"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
