import yt_dlp
import os
import subprocess

def get_stream_link(youtube_url):
    # Folder dhoondne ki koshish (Render environment ke liye)
    possible_paths = [
        os.path.join(os.getcwd(), 'bgutil-ytdlp-pot-provider', 'server'),
        os.path.join(os.getcwd(), 'server'),
        '/opt/render/project/src/bgutil-ytdlp-pot-provider/server'
    ]
    
    server_path = None
    for path in possible_paths:
        if os.path.exists(path):
            server_path = path
            break

    if not server_path:
        return "Error: Server folder not found in project"

    ydl_opts = {
        'format': 'ba[ext=m4a]/140/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'js_runtimes': ['node'],
        'extractor_args': {
            'youtubepot-bgutilscript': {
                'server_home': server_path
            },
            'youtube': {
                'player_client': ['web_music', 'web'],
                'allow_remote_strings': True
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return info.get('url')
    except Exception as e:
        return f"Error: {str(e)}"
