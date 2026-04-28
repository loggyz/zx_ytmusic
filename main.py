import yt_dlp
import os

def get_stream_link(youtube_url):
    # Render par project root path nikalna
    project_root = os.getcwd()
    server_path = os.path.join(project_root, 'bgutil-ytdlp-pot-provider', 'server')

    ydl_opts = {
        # Best audio m4a dhoondega, nahi toh koi bhi best audio
        'format': 'ba[ext=m4a]/140/bestaudio/best',
        
        # Logs dekhne ke liye (Debugging ke liye true rakhein)
        'verbose': True,
        
        # Node.js runtime specify karna zaroori hai
        'js_runtimes': ['node'],
        
        'extractor_args': {
            'youtubepot-bgutilscript': {
                'server_home': server_path
            },
            'youtube': {
                # web_music se m4a milne ke chances 100% hain
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

# Example Use:
# url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
# print(get_stream_link(url))
