import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID provided"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"

    # Documentation ke mutabiq 'tv' client aur cookies ka combo best hai
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        
        # Cookies pass karne ka standard tareeka
        'cookiefile': 'cookies.txt', 
        
        'extractor_args': {
            'youtube': {
                # TV client authentication ko zyada halke mein leta hai
                'player_client': ['tv', 'android'],
                'player_skip': ['web', 'web_music', 'ios'],
            },
            'youtubepot-bgutilhttp': {
                'base_url': 'http://127.0.0.1:4416' 
            }
        },
        
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        },
        
        'compat_opts': {'remote-components': 'ejs:github'},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Info extraction
            info = ydl.extract_info(url, download=False)
            
            # Agar direct info['url'] na mile toh formats check karo
            audio_url = info.get('url')
            if not audio_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('url'):
                        audio_url = f['url']
                        break
            
            if audio_url:
                return jsonify({"status": "success", "url": audio_url, "title": info.get('title')})
            
            return jsonify({"status": "error", "message": "Extraction failed after cookies"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
