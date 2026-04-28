import os
from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

# Global Proxy setup taaki Python leak na kare
PROXY = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"
os.environ['HTTP_PROXY'] = PROXY
os.environ['HTTPS_PROXY'] = PROXY

def get_yt_link(video_url):
    project_root = os.getcwd()
    # Path dhoondne ka naya tarika
    server_path = os.path.join(project_root, 'bgutil-ytdlp-pot-provider', 'server')
    
    ydl_opts = {
        'proxy': PROXY,
        'format': '140', 
        'quiet': False, # Debugging ke liye ise False kiya hai
        'no_warnings': False,
        'js_runtimes': {'node': {}},
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
