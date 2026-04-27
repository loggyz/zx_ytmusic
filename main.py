import yt_dlp
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/get_stream')
def get_stream():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "Abey ID toh de pehle!"}), 400

    # Tera magic backdoor URL
    target_url = f"http://googleusercontent.com/youtube.com/{video_id}"
    
    # Tera Owl Proxy
    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

    ydl_opts = {
        'proxy': proxy_url,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # Termux wala logic: No specific client, just the legacy path
        'format': 'bestaudio/best',
        # User agent fix: Google servers ke liye 'trusted' dikhna zaroori hai
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'http_headers': {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extracting information from the backdoor URL
            info = ydl.extract_info(target_url, download=False)
            
            # Hamein wahi 'url' nikalna hai jo tune Termux pe dekha tha
            stream_url = info.get('url')
            
            if stream_url:
                return jsonify({
                    "status": "success",
                    "stream_url": stream_url,
                    "title": info.get('title', 'Unknown')
                })
            else:
                return jsonify({"error": "Stream link nahi mila, bypass fail ho gaya"}), 500
                
    except Exception as e:
        # Error handling taaki pata chale kahan phat raha hai
        error_msg = str(e)
        return jsonify({
            "status": "error",
            "message": error_msg
        }), 502

if __name__ == '__main__':
    # Render port 10000 use karta hai
    app.run(host='0.0.0.0', port=10000)
