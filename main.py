import os
import sys
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
    print(f"[DEBUG] Starting extraction for ID: {video_id}", flush=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': False,
        'proxy': PROXY,
        # --- YE LINES IMPORTANT HAIN ---
        'allow_remote_strings': True, # Remote solver download karne ke liye
        'extractor_args': {
            'youtube': {
                'player_client': ['web_embedded', 'ios'],
                # Inko dhyan se check karo
                'remote_components': ['ejs:github'], 
                'skip': ['hls', 'dash'] # Faltu cheezein skip karke speed badhayega
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
                print(f"[SUCCESS] URL generated for {video_id}", flush=True)
                return info['url']
    except Exception as e:
        print(f"--- BYPASS ERROR ---\nDetails: {str(e)}\n--- END ERROR ---", flush=True)
    return None

@app.route('/')
def home():
    return {"status": "Live", "js": os.path.exists(os.path.join(SERVER_HOME, 'build', 'main.js'))}

@app.route('/get_audio')
def get_audio():
    video_id = request.args.get('id')
    if not video_id: return jsonify({"error": "No ID"}), 400
    url = get_audio_url(video_id)
    if url: return jsonify({"url": url})
    return jsonify({"error": "Bypass failed", "tip": "Check Logs for Remote Component warning"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
