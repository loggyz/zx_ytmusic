import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID"}), 400

    # Documentation ke mutabiq Video ID bound request
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        # RULE 1: Documentation force kar rahi hai ba[ext=m4a]
        'format': 'ba[ext=m4a]/bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        
        # RULE 2: Cookies for GVS (Render IP bypass)
        'cookiefile': 'cookies.txt', 
        
        'extractor_args': {
            # RULE 3: Mandatory MWEB client as per Wiki
            'youtube': {
                'player_client': ['mweb'],
                'player_skip': ['web', 'ios', 'android', 'tv'],
            },
            # RULE 4: PO Token Provider integration for GVS
            'youtubepot-bgutilhttp': {
                'base_url': 'http://127.0.0.1:4416' 
            }
        },
        
        'http_headers': {
            # Mobile Web User-Agent (Safari on iPhone)
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        },
        
        # REQUIRED for the JS Challenge bypass
        'compat_opts': {'remote-components': 'ejs:github'},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Info extraction
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"status": "error", "message": "No Response"}), 500

            # Step 5: Format specific searching
            audio_url = None
            if 'formats' in info:
                # Sirf M4A filter
                for f in info['formats']:
                    if f.get('ext') == 'm4a' and f.get('acodec') != 'none':
                        audio_url = f['url']
                        break
            
            # Fallback agar M4A block ho (Rare with mweb)
            if not audio_url:
                audio_url = info.get('url')

            if audio_url:
                return jsonify({
                    "status": "success",
                    "url": audio_url,
                    "title": info.get('title'),
                    "client": "mweb"
                })
            
            return jsonify({"status": "error", "message": "M4A extraction failed on GVS step"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
