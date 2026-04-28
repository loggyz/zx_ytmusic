import os
import subprocess
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# Global Proxy
PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"
os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY

def get_yt_link(video_url):
    # 1. Node Path find karna
    try:
        node_path = subprocess.check_output(['which', 'node']).decode().strip()
    except:
        node_path = 'node'

    # 2. Server Path ko "Force" dhoondna
    # Hum current directory se start karke exact folder dhoondenge
    cwd = os.getcwd()
    potential_path = ""
    for root, dirs, files in os.walk(cwd):
        if 'server' in dirs and ('bgutil' in root or 'pot' in root):
            potential_path = os.path.join(root, 'server')
            break
    
    # Agar walk fail ho jaye toh default
    if not potential_path:
        potential_path = os.path.join(cwd, 'bgutil-ytdlp-pot-provider', 'server')

    ydl_opts = {
        'proxy': PROXY,
        'format': '140', # Pure m4a
        'quiet': True,
        'no_warnings': True,
        'js_runtimes': {
            'node': {'path': node_path}
        },
        'extractor_args': {
            'youtubepot-bgutilscript': {
                'server_home': potential_path
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
        # Debugging ke liye hum yahan error message return karenge
        return f"Error: {str(e)}"

@app.route('/get_audio')
def get_audio():
    url = request.args.get('url', 'dQw4w9WgXcQ')
    stream_link = get_yt_link(url)
    return jsonify({"stream_url": stream_link})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
