import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_HOME = os.path.join(BASE_DIR, 'bgutil-server', 'server')

def get_audio_url(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # --- YAHAN SE DHYAN DENA (Spacing 4 spaces honi chahiye) ---
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'mweb'],
            },
            'youtubepot-bgutilscript': {
                'server_home': SERVER_HOME
            }
        },
        'js_runtimes': {'node': {}} 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if info and 'url' in info:
                return info['url']
    except Exception as e:
        print(f"\n--- !!! BYPASS ERROR !!! ---\nDetails: {str(e)}\n--- !!! END ERROR !!! ---\n")
    return None

@app.route('/')
def home():
    js_path = os.path.join(SERVER_HOME, 'build', 'main.js')
    return {
        "status": "Live",
        "js_file_exists": os.path.exists(js_path)
    }

@app.route('/get_audio')
def get_audio():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "No ID provided"}), 400
    url = get_audio_url(video_id)
    if url:
        return jsonify({"url": url})
    return jsonify({"error": "Bypass failed"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
