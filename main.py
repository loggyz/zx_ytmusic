import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID"}), 400

    # Documentation ke mutabiq proper URL format
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Path to your bgutil server (Render environment path)
    # Note: Ensure this matches your folder structure
    current_dir = os.getcwd()
    server_path = os.path.join(current_dir, 'bgutil-ytdlp-pot-provider', 'server')

    ydl_opts = {
        'verbose': True, # Debugging ke liye on rakha hai
        'format': 'ba[ext=m4a]/bestaudio/best',
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt',
        
        # FIX 1: JS Challenge solve karne ke liye Node.js ko force karna
        'javascript_runtimes': ['node'],
        
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb'],
                'player_skip': ['web', 'ios', 'android', 'tv'],
            },
            # FIX 2: Provider ko manual path dena taaki detect ho sake
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
            
            return jsonify({"status": "error", "message": "No playable audio format found"}), 500

    except Exception as e:
        # Logs mein poora error dikhega
        print(f"ERROR: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Render default port
    app.run(host='0.0.0.0', port=10000)
