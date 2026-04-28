import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

# --- FLASK APP SETUP ---
app = Flask(__name__) # Gunicorn isi 'app' ko dhund raha hai
CORS(app)

# --- PATH CONFIGURATION ---
# Render par hum project ko isi folder mein clone karenge
HOME_PATH = os.environ.get('HOME', '/opt/render')
SERVER_HOME = os.path.join(HOME_PATH, 'bgutil-server/server')

def get_audio_url(video_id):
    # Standard YouTube URL logic
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'mweb'],
            },
            # Strict Script Method for PO Token
            'youtubepot-bgutilscript': {
                'server_home': SERVER_HOME
            }
        },
        # Render par Node.js use karne ke liye
        'js_runtimes': ['node']
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if info and 'url' in info:
                return info['url']
    except Exception as e:
        print(f"Bypass Error: {str(e)}")
    return None

@app.route('/')
def home():
    return "ZX-YTMusic Server is Live!"

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "ID missing"}), 400
    
    url = get_audio_url(video_id)
    if url:
        return jsonify({"url": url})
    else:
        return jsonify({"error": "YouTube security bypass failed"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
