from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

def get_yt_link(video_url):
    project_root = os.getcwd()
    # Path logic for Render
    server_path = os.path.join(project_root, 'bgutil-ytdlp-pot-provider', 'server')
    if not os.path.exists(server_path):
        server_path = os.path.join(project_root, 'server')

    # Aapki OwlProxy Details
    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

    ydl_opts = {
        'proxy': proxy_url,
        # FORCE: Sirf itag 140 (m4a) dhoondo. Agar na mile toh error do (taaki humein pata chale)
        'format': '140/bestaudio[ext=m4a]', 
        'quiet': True,
        'js_runtimes': {'node': {}},
        'extractor_args': {
            'youtubepot-bgutilscript': {'server_home': server_path},
            'youtube': {
                # Sirf web_music rakho, android/web hata do
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
    return "Music Server with Residential Proxy: Active ✅"

@app.route('/get_audio')
def get_audio():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    stream_link = get_yt_link(url)
    return jsonify({"stream_url": stream_link})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
