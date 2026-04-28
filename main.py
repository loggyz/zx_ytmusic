from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

def get_yt_link(video_url):
    project_root = os.getcwd()
    server_path = os.path.join(project_root, 'bgutil-ytdlp-pot-provider', 'server')
    
    # OwlProxy Details
    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

    ydl_opts = {
        'proxy': proxy_url,
        # FORCE: Sirf itag 140 (m4a) mangna hai
        'format': '140', 
        'quiet': True,
        'no_warnings': True,
        'js_runtimes': {'node': {}},
        'extractor_args': {
            'youtubepot-bgutilscript': {'server_home': server_path},
            'youtube': {
                # STRICT: Sirf web_music (YouTube Music) client use hoga
                'player_client': ['web_music'],
                'allow_remote_strings': True
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            url = info.get('url')
            # Double check: Agar galti se link mein itag=18 aa gaya toh filter kar do
            if "itag=18" in url or "mime=video" in url:
                return "Error: YouTube refused m4a and sent MP4."
            return url
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/get_audio')
def get_audio():
    url = request.args.get('url', 'dQw4w9WgXcQ')
    stream_link = get_yt_link(url)
    return jsonify({"stream_url": stream_link})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
