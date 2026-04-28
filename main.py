import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_HOME = os.path.join(BASE_DIR, 'bgutil-server', 'server')

def get_audio_url(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
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
        # Purana format: ['node'] -> GALAT
        # Naya format: {'node': {}} -> SAHI
        'js_runtimes': {'node': {}} 
    }


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if info and 'url' in info:
                return info['url']
    except Exception as e:
        # Yeh print statements Render Dashboard ke Logs tab mein dikhenge
        print(f"\n--- !!! BYPASS ERROR !!! ---")
        print(f"Details: {str(e)}")
        print(f"--- !!! END ERROR !!! ---\n")
    return None

@app.route('/')
def home():
    # Check if main.js is actually there
    js_path = os.path.join(SERVER_HOME, 'build', 'main.js')
    return {
        "status": "Live",
        "js_file_exists": os.path.exists(js_path),
        "js_path": js_path
    }

@app.route('/get_audio')
def get_audio():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "No ID provided"}), 400
        
    url = get_audio_url(video_id)
    if url:
        return jsonify({"url": url})
    
    return jsonify({
        "error": "YouTube security bypass failed",
        "msg": "Check Render Logs for 'BYPASS ERROR'"
    }), 500
