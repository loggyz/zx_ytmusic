import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

# CONFIGURATION
SERVER_PATH = "/opt/render/project/src/bgutil-ytdlp-pot-provider/server/src/main.ts"
# Agar proxy use karni hai toh yahan dalo, warna khali chhod do ''
PROXY_URL = '' 

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No URL/ID provided"}), 400

    # URL agar sirf ID hai toh use full banayein
    if not video_id.startswith('http'):
        url = f"https://www.youtube.com/watch?v={video_id}"
    else:
        url = video_id

    ydl_opts = {
        'proxy': PROXY_URL if PROXY_URL else None,
        'format': 'bestaudio/best', 
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
        
        'extractor_args': {
            'youtube': {
                # Yahan hum web_music ko priority de rahe hain
                'player_client': ['web_music', 'android'],
                'player_skip': ['webpage', 'ios'],
            },
            'youtubepot-bgutilscript': {
                'server_home': SERVER_PATH,
                'server_address': 'http://127.0.0.1:4416' 
            }
        },
        
        # Web Music ke liye optimized headers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://music.youtube.com/',
            'Origin': 'https://music.youtube.com/',
        },
        
        'compat_opts': {'remote-components': 'ejs:github'},
        'youtube_include_dash_manifest': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Info extract kar rahe hain bina download kiye
            info = ydl.extract_info(url, download=False)
            
            if info is None:
                return jsonify({"status": "error", "message": "YouTube ne koi data nahi diya (IP Block?)"}), 500
            
            # Safe tareeke se URL nikalna
            audio_url = info.get('url')
            if not audio_url and 'formats' in info:
                # Agar main 'url' na mile toh formats mein check karo
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
            else:
                return jsonify({"status": "error", "message": "Audio link nahi mil paya"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Flask port 10000 par chalega (Render default)
    app.run(host='0.0.0.0', port=10000)
