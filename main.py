import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- PO TOKEN CONFIGURATION ---
# Render ke environment ke hisaab se home path set karein
HOME_PATH = os.environ.get('HOME', '/opt/render')
# Build command mein humne isi path par clone kiya hai
SERVER_HOME = os.path.join(HOME_PATH, 'bgutil-server/server')

def get_audio_url(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': False,  # Logs dekhne ke liye True rakha hai
        'no_warnings': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'mweb', 'web_embedded'],
            },
            # Ye wahi "Chabi" hai jo humne Termux mein test ki thi
            'youtubepot-bgutilscript': {
                'server_home': SERVER_HOME
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info bina download kiye
            info = ydl.extract_info(video_url, download=False)
            if info and 'url' in info:
                return info['url']
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
    return None

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "No ID provided"}), 400
    
    url = get_audio_url(video_id)
    if url:
        return jsonify({"url": url})
    else:
        return jsonify({"error": "Failed to bypass YouTube security"}), 500

if __name__ == '__main__':
    # Render pe port dynamic hota hai
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
