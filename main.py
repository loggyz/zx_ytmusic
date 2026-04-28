import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# --- NEW RELATIVE PATH LOGIC ---
# Ye project folder se ek kadam peeche ja kar bgutil-server dhoondega
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_HOME = os.path.join(BASE_DIR, 'bgutil-server', 'server')

@app.route('/')
def home():
    # Debugging ke liye check karein
    exists = os.path.exists(SERVER_HOME)
    build_js_exists = os.path.exists(os.path.join(SERVER_HOME, 'build', 'main.js'))
    return {
        "status": "Live",
        "provider_path": SERVER_HOME,
        "folder_exists": exists,
        "build_js_exists": build_js_exists
    }

def get_audio_url(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'mweb'],
            },
            'youtubepot-bgutilscript': {
                'server_home': SERVER_HOME
            }
        },
        'js_runtimes': ['node']
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('url')
    except Exception as e:
        print(f"Bypass Error: {str(e)}")
        return None

@app.route('/get_audio')
def get_audio():
    video_id = request.args.get('id')
    url = get_audio_url(video_id)
    if url:
        return jsonify({"url": url})
    return jsonify({"error": "YouTube security bypass failed"}), 500
