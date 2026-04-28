from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

def get_yt_link(video_url):
    project_root = os.getcwd()
    # Path for Render
    server_path = os.path.join(project_root, 'bgutil-ytdlp-pot-provider', 'server')
    if not os.path.exists(server_path):
        server_path = os.path.join(project_root, 'server')

    # Proxy with Location changed to IN (India)
    proxy_url = "http://WT5vlVZQfW10_custom_zone_IN_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

    ydl_opts = {
        'proxy': proxy_url,
        # Termux ki tarah strict m4a priority
        'format': 'ba[ext=m4a]/140', 
        'quiet': True,
        'js_runtimes': {'node': {}},
        'extractor_args': {
            'youtubepot-bgutilscript': {'server_home': server_path},
            'youtube': {
                # CHANGE: web_music ke bajaye ios aur web use karo
                # ios client m4a dene mein sabse kam nakhre karta hai
                'player_client': ['ios', 'web'],
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
    return "Music Server IN-Proxy Mode: Active ✅"

@app.route('/get_audio')
def get_audio():
    url = request.args.get('url', 'dQw4w9WgXcQ')
    stream_link = get_yt_link(url)
    return jsonify({"stream_url": stream_link})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
