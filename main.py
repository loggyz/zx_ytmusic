import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        # 'best' mangenge, audio hum baad mein khud dhoondhenge
        'format': 'best', 
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
        'source_address': '0.0.0.0', # Force IPv4 (Render ke IPv6 aksar block hote hain)
        
        'extractor_args': {
            'youtube': {
                # Mix of all possible bypass clients
                'player_client': ['mweb', 'android_vr', 'web_music'],
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
            # list_formats=True hata do, direct extract karo
            info = ydl.extract_info(url, download=False)
            
            # Agar best audio nahi mil raha, toh saare formats scan karo
            audio_url = None
            if 'formats' in info:
                # 1. Sabse pehle koi bhi audio stream dhoondo
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        audio_url = f['url']
                        break
                
                # 2. Agar audio-only nahi hai, toh video+audio stream utha lo
                if not audio_url:
                    for f in info['formats']:
                        if f.get('acodec') != 'none':
                            audio_url = f['url']
                            break

            if audio_url:
                return jsonify({
                    "status": "success",
                    "url": audio_url,
                    "title": info.get('title')
                })
            
            return jsonify({"status": "error", "message": "YouTube hidden all streams from this IP"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
