import os
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

HOME_PATH = os.environ.get('HOME', '/opt/render')
SERVER_HOME = os.path.join(HOME_PATH, 'bgutil-server/server')

def get_audio_url(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # --- DEBUG LOGS ---
    print(f"DEBUG: Checking path: {SERVER_HOME}")
    print(f"DEBUG: Path exists? {os.path.exists(SERVER_HOME)}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': False,
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'mweb', 'web_embedded'],
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
        print(f"CRITICAL ERROR: {str(e)}")
        return None

@app.route('/')
def home():
    # Ye route check karne ke liye ki server path sahi dhoond raha hai ya nahi
    status = "Exists" if os.path.exists(SERVER_HOME) else "NOT FOUND"
    return f"Server Live. Provider Path: {SERVER_HOME} ({status})"

@app.route('/get_audio')
def get_audio():
    video_id = request.args.get('id')
    url = get_audio_url(video_id)
    if url:
        return jsonify({"url": url})
    return jsonify({"error": "YouTube security bypass failed"}), 500
