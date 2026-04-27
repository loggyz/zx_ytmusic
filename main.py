from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

def get_audio_url(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Cookies ka path (Make sure ye file teri Git repo me root par ho)
    cookies_path = 'cookies.txt' 

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'cookiefile': cookies_path if os.path.exists(cookies_path) else None,
        'extractor_args': {
            'youtube': {
                # 'mweb' aur 'web' clients abhi sabse stable hain
                'player_client': ['mweb', 'web'],
                # Plugin (bgutil) apne aap po_token fetch karke inject kar degi
            }
        },
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info['url']
    except Exception as e:
        print(f"Error fetching URL for {video_id}: {str(e)}")
        return None

@app.route('/get_url', methods=['GET'])
def get_url():
    v_id = request.args.get('id')
    if not v_id:
        return jsonify({"error": "No ID provided"}), 400
    
    audio_url = get_audio_url(v_id)
    if audio_url:
        return jsonify({"url": audio_url})
    return jsonify({"error": "Failed to fetch audio URL"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
