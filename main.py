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
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': False,
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['web_embedded', 'web', 'mweb'],
                'player_skip': ['webpage', 'configs'], # Speed up extraction
            },
            'youtubepot-bgutilscript': {
                'server_home': SERVER_HOME
            }
        },
        # Render par node ka path verify karne ke liye multiple options
        'js_runtimes': ['node']
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Force log extraction to see what's happening
            info = ydl.extract_info(video_url, download=False)
            if info and 'url' in info:
                return info['url']
    except Exception as e:
        # Ye print ab Render ke "Logs" tab mein pakka dikhega
        print(f"--- BYPASS CRITICAL ERROR ---")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"--- END ERROR ---")
    return None

@app.route('/')
def home():
    return {
        "status": "Live",
        "provider_path": SERVER_HOME,
        "build_js_exists": os.path.exists(os.path.join(SERVER_HOME, 'build', 'main.js'))
    }

@app.route('/get_audio')
def get_audio():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "No ID provided"}), 400
        
    url = get_audio_url(video_id)
    if url:
        return jsonify({"url": url})
    
    # Is baar hum thoda zyada info denge error mein
    return jsonify({
        "error": "YouTube security bypass failed",
        "debug_info": "Check Render Logs for 'BYPASS CRITICAL ERROR'"
    }), 500
