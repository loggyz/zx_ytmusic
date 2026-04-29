import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

# Path to the POT provider server
SERVER_PATH = "/opt/render/project/src/bgutil-ytdlp-pot-provider/server/src/main.ts"

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID provided"}), 400

    # Clean URL construction
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        
        # GITHUB PE DALI HUI COOKIES FILE USE KAR RAHE HAIN
        'cookiefile': 'cookies.txt', 
        
        'extractor_args': {
            'youtube': {
                # Mobile clients + PO Token = Best Bypass
                'player_client': ['ios', 'android'],
                'player_skip': ['web', 'web_music'],
            },
            'youtubepot-bgutilhttp': {
                'base_url': 'http://127.0.0.1:4416' 
            }
        },
        
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        },
        
        'compat_opts': {'remote-components': 'ejs:github'},
        'youtube_include_dash_manifest': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"status": "error", "message": "YouTube response was empty"}), 500
            
            # Fetching the best audio URL from extracted info
            audio_url = info.get('url')
            if not audio_url and 'formats' in info:
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('url'):
                        audio_url = f['url']
                        break
            
            if audio_url:
                return jsonify({
                    "status": "success",
                    "url": audio_url,
                    "title": info.get('title'),
                    "duration": info.get('duration')
                })
            
            return jsonify({"status": "error", "message": "Could not find audio URL"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Running on port 10000 for Render
    app.run(host='0.0.0.0', port=10000)
