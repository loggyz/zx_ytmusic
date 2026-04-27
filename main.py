import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/get_stream')
def get_stream():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "Abey ID toh de!"}), 400

    # Ye base URL hai jo yt-dlp internal use karta hai
    # Isko direct browser mein kholne pe 404 aayega, 
    # par yt-dlp isse 'Valid' stream link nikaal lega.
    target_url = f"https://www.youtube.com/watch?v={video_id}"
    
    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

    ydl_opts = {
        'proxy': proxy_url,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'format': 'bestaudio/best',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Termux pe jo '-g' command hai, wo yahan 'extract_info' hai
            info = ydl.extract_info(target_url, download=False)
            
            # Ye 'stream_url' hoga ekdum VALID aur CLICKABLE link
            stream_url = info.get('url')
            
            if stream_url:
                return jsonify({
                    "status": "success",
                    "stream_url": stream_url, # Ye link browser mein chalega
                    "title": info.get('title')
                })
            else:
                return jsonify({"status": "error", "message": "Valid link nahi mila"}), 500
                
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
