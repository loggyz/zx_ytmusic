import os
import yt_dlp

# Render environment paths
HOME_PATH = os.environ.get('HOME', '/opt/render')
SERVER_HOME = os.path.join(HOME_PATH, 'bgutil-server/server')

def get_audio_url(video_id):
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'nocheckcertificate': True,
        'quiet': False,
        'extractor_args': {
            'youtube': {
                # Sirf wahi clients use karein jo PO Token maangte hain
                'player_client': ['web', 'mweb'],
            },
            # Yahan hum yt-dlp ko bata rahe hain ki "Bhai, HTTP mat dhoondo, ye rahi script"
            'youtubepot-bgutilscript': {
                'server_home': SERVER_HOME
            }
        },
        # Render par Node.js ka path aksar yahan hota hai
        'js_runtimes': ['node'] 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info.get('url')
    except Exception as e:
        print(f"CRITICAL DEBUG: {str(e)}")
    return None
