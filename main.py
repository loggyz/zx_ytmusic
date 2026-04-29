import os
import subprocess
import shutil
import yt_dlp
from flask import Flask, request, jsonify

# --- DETECTIVE SECTION: Yeh batayega asliyat kya hai ---
print("--- ENVIRONMENT SCAN START ---")
print(f"DEBUG: Current Directory: {os.getcwd()}")
try:
    node_loc = subprocess.check_output(['which', 'node']).decode().strip()
    print(f"DEBUG: Node is actually at: {node_loc}")
    # Mil gaya toh PATH mein force add karo
    os.environ["PATH"] += os.pathsep + os.path.dirname(node_loc)
except Exception as e:
    print(f"DEBUG: Node check failed: {e}")
print("--- ENVIRONMENT SCAN END ---")

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Dynamic path for bgutil
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, 'bgutil-ytdlp-pot-provider', 'server')

    ydl_opts = {
        'verbose': True,
        'format': 'ba[ext=m4a]/bestaudio/best',
        'quiet': False,
        'javascript_runtimes': ['node'],
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb'],
                'player_skip': ['web', 'ios', 'android', 'tv'],
            },
            'youtubepot-bgutilhttp': { 'base_url': 'http://127.0.0.1:4416' },
            'youtubepot-bgutilscript': { 'server_home': server_path }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({"status": "success", "url": info.get('url')})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
