import os
import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_audio', methods=['GET'])
def get_audio():
    video_id = request.args.get('url')
    if not video_id:
        return jsonify({"status": "error", "message": "No ID"}), 400

    # Clean URL logic
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'verbose': True,
        'format': 'ba[ext=m4a]/bestaudio/best', # m4a try karo, webm 403 zyada deta hai
        'nocheckcertificate': True,
        'proxy': 'http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778',
        
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'ios'], # Inka IP binding thoda loose hota hai
                'player_skip': ['web', 'android_vr'], 
            },
            'youtubepot-bgutilhttp': { 'base_url': 'http://127.0.0.1:4416' }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info and 'url' in info:
                return jsonify({
                    "status": "success",
                    "url": info['url'],
                    "title": info.get('title')
                })
            
            return jsonify({"status": "error", "message": "Could not extract URL"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
