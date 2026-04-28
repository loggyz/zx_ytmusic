from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

def get_yt_link(video_url):
    project_root = os.getcwd()
    server_path = os.path.join(project_root, 'bgutil-ytdlp-pot-provider', 'server')
    if not os.path.exists(server_path):
        server_path = os.path.join(project_root, 'server')

    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

    ydl_opts = {
        'proxy': proxy_url,
        # ISKO DHAYAN SE DEKHO: 
        # Pehle m4a (140), nahi toh mp4 (18), nahi toh sabse best jo available ho.
        # Strictness hata di hai taaki "Not Available" error na aaye.
        'format': '140/18/bestaudio/best',
        
        'quiet': True,
        'no_warnings': True,
        'js_runtimes': {'node': {}},
        'extractor_args': {
            'youtubepot-bgutilscript': {'server_home': server_path},
            'youtube': {
                # Sirf web_music par mat ruko, android aur web ko saath rakho
                'player_client': ['android', 'web', 'web_music'],
                'allow_remote_strings': True
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # force_generic_extractor hata diya hai taaki PO-Token sahi se kaam kare
            info = ydl.extract_info(video_url, download=False)
            return info.get('url')
    except Exception as e:
        # Last resort: bina proxy aur bina kisi format restriction ke try karo
        try:
            ydl_opts.pop('proxy', None)
            ydl_opts['format'] = 'best' 
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info.get('url')
        except Exception as e2:
            return f"Error: {str(e2)}"

@app.route('/')
def home():
    return "Music Server Final ✅"

@app.route('/get_audio')
def get_audio():
    url = request.args.get('url', 'dQw4w9WgXcQ')
    stream_link = get_yt_link(url)
    return jsonify({"stream_url": stream_link})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
