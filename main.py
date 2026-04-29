import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# 1. Proxy Setup (OwlProxy)
PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"
os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY

# 2. Paths (Jo humne abhi verify kiye hain)
BASE_PATH = "/opt/render/project/src/bgutil-ytdlp-pot-provider"
SERVER_PATH = f"{BASE_PATH}/server"
PLUGIN_PATH = f"{BASE_PATH}/plugin"

def get_yt_audio_link(video_url):
    ydl_opts = {
        'proxy': PROXY,
        'format': '140/bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
        'cookiefile': 'cookies.txt',
        'js_runtimes': {
            'node': {'path': 'node'} 
        },
        'extractor_args': {
            # Ye extractor logic ko server ka path batata hai
            'youtubepot-bgutilscript': {'server_home': SERVER_PATH},
            'youtube': {
                'player_client': ['web_music', 'web', 'android', 'ios'],
                'allow_remote_strings': True,
                'remote_control_ejs': 'github',
            }
        },
        'allow_unplayable_formats': True,
        'socket_timeout': 30,
        'retries': 5,
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Plugin folder ko manually register karne ki zarurat nahi hoti
            # agar wo yt_dlp_plugins folder ke andar sahi structure me ho.
            info = ydl.extract_info(video_url, download=False)
            return {
                "status": "success", 
                "title": info.get('title'),
                "stream_url": info.get('url'),
                "thumbnail": info.get('thumbnail')
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def home():
    return "ZX Music Engine: All Systems Operational (TRUE)"

@app.route('/get_audio')
def get_audio():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "No URL provided"}), 400
    
    result = get_yt_audio_link(video_url)
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
