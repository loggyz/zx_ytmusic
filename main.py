import yt_dlp
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/get_stream')
def get_stream():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "No ID provided"}), 400

    # Ye hai tera dhanshu bypass link jo Termux pe kaam kar raha hai
    # Isko hum as a 'URL' bhejenge, na ki as a 'Video ID'
    target_url = f"http://googleusercontent.com/youtube.com/{video_id}"
    
    proxy_url = "http://WT5vlVZQfW10_custom_zone_US_st__city_sid_88323983_time_5:2549275@change6.owlproxy.com:7778"

    ydl_opts = {
        'proxy': proxy_url,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # 'force_generic_extractor' hata diya hai kyunki wo link ko block kar raha tha
        # Isko as a 'youtube' request hi jane denge par is specific URL ke saath
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Seedha target_url extract kar rahe hain
            info = ydl.extract_info(target_url, download=False)
            
            # Jo lamba url tujhe Termux pe dikha tha, wo yahan 'url' key mein hoga
            stream_url = info.get('url')
            
            if stream_url:
                return jsonify({"stream_url": stream_url})
            else:
                return jsonify({"error": "Link extract nahi hua"}), 500
                
    except Exception as e:
        return jsonify({"error": str(e)}), 502

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
