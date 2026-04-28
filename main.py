import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_HOME = os.path.join(BASE_DIR, 'bgutil-server', 'server')
PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

def get_audio_url(video_id):
    # Try multiple URL variants
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        # Format ko thoda relax karte hain taaki koi bhi audio mil jaye
        'format': 'ba/b', 
        'proxy': PROXY,
        'quiet': False,
        'allow_remote_strings': True,
        'extractor_args': {
            'youtube': {
                # web_embedded sabse stable hai, ios backup ke liye
                'player_client': ['web_embedded', 'ios'],
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
            # extract_info calls our bgutil provider automatically
            info = ydl.extract_info(video_url, download=False)
            if info:
                # Direct URL ya formats mein se pehla link uthao
                url = info.get('url') or (info.get('formats', [{}])[0].get('url'))
                if url:
                    return {"url": url, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}
    return {"error": "No URL found in response", "success": False}

@app.route('/')
def home():
    # Final check before we hit bypass
    provider_ready = os.path.exists(os.path.join(SERVER_HOME, 'build', 'main.js'))
    return {
        "status": "Live",
        "po_token_provider": "READY" if provider_ready else "MISSING",
        "provider_path": SERVER_HOME
    }

@app.route('/get_audio')
def get_audio():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "No ID"}), 400
    
    result = get_audio_url(video_id)
    if result.get("success"):
        return jsonify({"url": result["url"]})
    
    return jsonify({
        "error": "Bypass Failed",
        "details": result.get("error")
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
