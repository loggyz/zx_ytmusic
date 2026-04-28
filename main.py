import os
import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_HOME = os.path.join(BASE_DIR, 'bgutil-server', 'server')

def get_audio_url(video_id):
    # Embedded URL block hone ke chances kam hote hain
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': False,
        # Ye line un missing components ko download karegi jo logs mein error de rahe the
        'allow_remote_strings': True,
        'extractor_args': {
            'youtube': {
                # 'web_embedded' sabse zyada stable hai IP block ke waqt
                'player_client': ['web_embedded'],
                'remote_components': 'ejs:github',
            },
            'youtubepot-bgutilscript': {
                'server_home': SERVER_HOME
            }
        },
        'js_runtimes': {'node': {}} 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if info and 'url' in info:
                return info['url']
    except Exception as e:
        print(f"\n--- !!! BYPASS ERROR !!! ---\nDetails: {str(e)}\n--- !!! END ERROR !!!\n")
    return None

@app.route('/')
def home():
    return {"status": "Live", "js_exists": os.path.exists(os.path.join(SERVER_HOME, 'build', 'main.js'))}

@app.route('/get_audio')
def get_audio():
    video_id = request.args.get('id')
    if not video_id: return jsonify({"error": "No ID"}), 400
    url = get_audio_url(video_id)
    if url: return jsonify({"url": url})
    return jsonify({"error": "Bypass failed", "reason": "YouTube Rate Limit or Signature Issue"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
