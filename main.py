import os
import subprocess
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# Global Proxy
PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"
os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY

def get_node_path():
    try:
        return subprocess.check_output(['which', 'node']).decode().strip()
    except:
        return '/usr/bin/node'

def get_yt_link(video_url):
    project_root = os.getcwd()
    node_path = get_node_path()
    
    # Precise Server Path Discovery
    server_path = ""
    for root, dirs, files in os.walk(project_root):
        if 'server' in dirs and 'bgutil' in root:
            server_path = os.path.join(root, 'server')
            break
    
    if not server_path:
        server_path = os.path.join(project_root, 'bgutil-ytdlp-pot-provider', 'server')

        ydl_opts = {
        'proxy': PROXY,
        'format': '140',
        'quiet': False,
        'no_warnings': False,
        # Naya Format: Dictionary ke andar dictionary
        'js_runtimes': {
            'node': {
                'path': node_path  # Yahan list nahi, direct path dena hai
            }
        },
        'extractor_args': {
            'youtubepot-bgutilscript': {'server_home': server_path},
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

@app.route('/get_audio')
def get_audio():
    url = request.args.get('url', 'dQw4w9WgXcQ')
    stream_link = get_yt_link(url)
    return jsonify({"stream_url": stream_link})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
