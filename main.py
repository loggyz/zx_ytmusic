import os
import shutil
import yt_dlp
from flask import Flask, request, jsonify

# --- STEP 1: NODE.JS PATH INJECTION ---
# Render par Node detection fix karne ke liye
node_path = shutil.which('node')
if node_path:
    os.environ["PATH"] += os.pathsep + os.path.dirname(node_path)

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID"}), 400

    # Clean URL logic
    url = f"https://www.youtube.com/watch?v={video_id}"

    # --- STEP 2: DYNAMIC PATH FOR BGUTIL ---
    # Isse "Script path doesn't exist" wala error khatam ho jayega
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, 'bgutil-ytdlp-pot-provider', 'server')

    ydl_opts = {
        'verbose': True,
        'format': 'ba[ext=m4a]/bestaudio/best',
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
        
        # --- STEP 3: FORCE NODE RUNTIME ---
        'javascript_runtimes': ['node'],
        
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb'],
                'player_skip': ['web', 'ios', 'android', 'tv'],
            },
            'youtubepot-bgutilhttp': {
                'base_url': 'http://127.0.0.1:4416' 
            },
            'youtubepot-bgutilscript': {
                'server_home': server_path
            }
        },
        
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        },
        
        'compat_opts': {'remote-components': 'ejs:github'},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"status": "error", "message": "Extraction failed"}), 500

            audio_url = None
            if 'formats' in info:
                for f in info['formats']:
                    # Specifically targeting M4A as per documentation
                    if f.get('ext') == 'm4a' and f.get('acodec') != 'none':
                        audio_url = f['url']
                        break
            
            if not audio_url:
                audio_url = info.get('url')

            if audio_url:
                return jsonify({
                    "status": "success",
                    "url": audio_url,
                    "title": info.get('title')
                })
            
            return jsonify({"status": "error", "message": "M4A format hide ho gaya hai"}), 500

    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
