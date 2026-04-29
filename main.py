import os
import sys
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# 1. Proxy Setup
PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"
os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY

# 2. Paths Setup
BASE_PATH = "/opt/render/project/src/bgutil-ytdlp-pot-provider"
SERVER_PATH = f"{BASE_PATH}/server"
PLUGIN_PATH = f"{BASE_PATH}/plugin"

# Plugin register karna zaroori hai
if PLUGIN_PATH not in sys.path:
    sys.path.insert(0, PLUGIN_PATH)

def get_yt_audio_link(video_url):
    ydl_opts = {
    'proxy': PROXY,
    'format': 'ba/best', # 'ba' matlab best audio (koi bhi extension ho)
    'quiet': True,
    'cookiefile': 'cookies.txt',
    'extractor_args': {
        'youtubepot-bgutilscript': {
            'server_home': SERVER_PATH,
            'server_address': 'http://127.0.0.1:4416' 
        }
    },
    'compat_opts': {'remote-components': 'ejs:github'},
    'nocheckcertificate': True,
    # Ye do lines zaroor add karo
    'ignoreerrors': True,
    'youtube_include_dash_manifest': True, 
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return {
                "status": "success", 
                "title": info.get('title'),
                "stream_url": info.get('url'),
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def home():
    return "ZX Music Engine: Challenge Solver Armed!"

@app.route('/get_audio')
def get_audio():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400
    return jsonify(get_yt_audio_link(video_url))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
