from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__) # Gunicorn ko yahi chahiye

def get_yt_link(video_url):
    # Render ke folder structure ke hisaab se path setting
    project_root = os.getcwd()
    server_path = os.path.join(project_root, 'bgutil-ytdlp-pot-provider', 'server')
    
    # Agar path exist nahi karta toh fallback check
    if not os.path.exists(server_path):
        server_path = os.path.join(project_root, 'server')

    ydl_opts = {
        'format': 'ba[ext=m4a]/140/bestaudio/best',
        'quiet': True,
        'js_runtimes': ['node'],
        'extractor_args': {
            'youtubepot-bgutilscript': {
                'server_home': server_path
            },
            'youtube': {
                'player_client': ['web_music', 'web'],
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
    return "Music Server Active ✅"

@app.route('/get_audio')
def get_audio():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    stream_link = get_yt_link(url)
    return jsonify({"stream_url": stream_link})

if __name__ == "__main__":
    # Render hamesha PORT env variable deta hai
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
