from flask import Flask, request, jsonify
import yt_dlp
import os
import sys

app = Flask(__name__)

def get_yt_link(video_url):
    # Render paths fix
    project_root = os.getcwd()
    # Hum directly search karenge ki 'server' folder kahan hai
    server_path = ""
    for root, dirs, files in os.walk(project_root):
        if 'server' in dirs and 'bgutil-ytdlp-pot-provider' in root:
            server_path = os.path.join(root, 'server')
            break
    
    if not server_path:
        server_path = os.path.join(project_root, 'bgutil-ytdlp-pot-provider', 'server')

    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

    ydl_opts = {
        'proxy': proxy_url,
        'format': '140', 
        'quiet': True,
        'no_warnings': True,
        # Force it to use the system node
        'js_runtimes': {'node': {}},
        'extractor_args': {
            'youtubepot-bgutilscript': {
                'server_home': server_path
            },
            'youtube': {
                'player_client': ['web_music'],
                'allow_remote_strings': True
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('url')
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def home():
    return "Server is Up"

@app.route('/get_audio')
def get_audio():
    # URL parameter ya default test video
    url = request.args.get('url', 'dQw4w9WgXcQ')
    stream_link = get_yt_link(url)
    if "Error" in stream_link:
        return jsonify({"stream_url": stream_link}), 500
    return jsonify({"stream_url": stream_link})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
