import os
import sys
import traceback
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_HOME = os.path.join(BASE_DIR, 'bgutil-server', 'server')
PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

def get_audio_url(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'proxy': PROXY,
        'quiet': False,
        'allow_remote_strings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios'],
                'remote_components': ['ejs:github'],
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
                return {"url": info['url'], "success": True}
    except Exception as e:
        # Pura error detail nikalne ke liye
        error_msg = str(e)
        full_trace = traceback.format_exc()
        return {"error": error_msg, "trace": full_trace, "success": False}

@app.route('/')
def home():
    js_path = os.path.join(SERVER_HOME, 'build', 'main.js')
    return {
        "status": "Live",
        "bgutil_built": os.path.exists(js_path),
        "path_checked": SERVER_HOME
    }

@app.route('/get_audio')
def get_audio():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "No ID"}), 400
    
    result = get_audio_url(video_id)
    if result.get("success"):
        return jsonify({"url": result["url"]})
    else:
        # Ab logs ki tension nahi, error seedha browser mein dikhega
        return jsonify({
            "error": "Bypass Failed",
            "details": result.get("error"),
            "server_side_trace": result.get("trace")
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
