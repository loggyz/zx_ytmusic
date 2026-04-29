import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID provided"}), 400

    # Documentation ke mutabiq full URL
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        # SPECIFIC M4A TARGET: Documentation ke hisaab se 'ba[ext=m4a]' use kar rahe hain
        'format': 'bestaudio[ext=m4a]/ba[ext=m4a]/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt', 
        
        'extractor_args': {
            'youtube': {
                # MWEB aur ANDROID_VR: Yehi dono m4a streams provide karte hain POT ke saath
                'player_client': ['mweb', 'android_vr'],
                'player_skip': ['web', 'ios', 'android'],
            },
            'youtubepot-bgutilhttp': {
                'base_url': 'http://127.0.0.1:4416' 
            }
        },
        
        'http_headers': {
            # Mobile Web User-Agent
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1',
        },
        
        'compat_opts': {'remote-components': 'ejs:github'},
        'youtube_include_dash_manifest': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"status": "error", "message": "YouTube failed to respond"}), 500

            # Extraction Logic for M4A
            audio_url = None
            if 'formats' in info:
                # Pehle M4A dhoondo
                for f in info['formats']:
                    if f.get('ext') == 'm4a' and f.get('acodec') != 'none':
                        audio_url = f['url']
                        break
                
                # Agar m4a nahi mila toh koi bhi audio (fallback)
                if not audio_url:
                    for f in info['formats']:
                        if f.get('acodec') != 'none':
                            audio_url = f['url']
                            break
            
            # Final Fallback
            if not audio_url:
                audio_url = info.get('url')

            if audio_url:
                return jsonify({
                    "status": "success",
                    "url": audio_url,
                    "title": info.get('title'),
                    "ext": info.get('ext', 'unknown')
                })
            
            return jsonify({"status": "error", "message": "MWEB failed to serve M4A"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
