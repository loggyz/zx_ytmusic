import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# 1. Proxy Setup (OwlProxy)
PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"
os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY

# 2. Render Path Setup
# Render par hamara folder isi location par hota hai
BGUTIL_SERVER_PATH = "/opt/render/project/src/bgutil-ytdlp-pot-provider/server"

def get_yt_audio_link(video_url):
        ydl_opts = {
        'proxy': PROXY,
        'format': '140',
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'js_runtimes': {
            'node': {'path': 'node'} 
        },
        'extractor_args': {
            'youtubepot-bgutilscript': {'server_home': BGUTIL_SERVER_PATH},
            'youtube': {
                'player_client': ['web_music', 'web', 'android'], # Client list badhao
                'allow_remote_strings': True,
                # Ye line EJS warnings ko solve karegi
                'remote_control_ejs': 'github', 
            }
        },
        # Challenge solving ke liye ye zaroori hai
        'allow_unplayable_formats': True,
        'socket_timeout': 30,
        'retries': 5,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return {"status": "success", "stream_url": info.get('url')}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def home():
    return "ZX Music Engine is Live!"

@app.route('/get_audio')
def get_audio():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400
    
    result = get_yt_audio_link(video_url)
    return jsonify(result)

if __name__ == "__main__":
    # Render default port 10000 use karta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
