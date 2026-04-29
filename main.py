import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID"}), 400

    # Ye wahi URL hai jisse pehle link nikla tha
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        # 'best' isliye taaki agar bestaudio na mile toh video hi utha le (audio extract ho jayega)
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        
        # Cookies are mandatory now for Render IP
        'cookiefile': 'cookies.txt', 
        
        'extractor_args': {
            # Documentation ke hisaab se Provider link
            'youtubepot-bgutilhttp': {
                'base_url': 'http://127.0.0.1:4416' 
            },
            # Hum clients ko default pe chhod denge, lekin web_music ko priority denge
            'youtube': {
                'player_client': ['android', 'web_music', 'ios'],
                'player_skip': ['web'], # Bas main 'web' skip kar rahe hain bot check se bachne ke liye
            }
        },
        
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
        
        'compat_opts': {'remote-components': 'ejs:github'},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First attempt: Full extraction
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"status": "error", "message": "No response"}), 500

            # Direct URL check
            audio_url = info.get('url')
            
            # Agar direct URL nahi hai, toh formats dhoondo (Yahi fix hai)
            if not audio_url and 'formats' in info:
                # Sabse pehle acodec check karo
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        audio_url = f['url']
                        break
                # Agar tab bhi na mile, toh koi bhi format jo chal jaye
                if not audio_url:
                    audio_url = info['formats'][0]['url']
            
            if audio_url:
                return jsonify({
                    "status": "success",
                    "url": audio_url,
                    "title": info.get('title')
                })
            
            return jsonify({"status": "error", "message": "Could not find any playable URL"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
