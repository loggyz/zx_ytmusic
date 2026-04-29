import os

def check_paths():
    base_path = "/opt/render/project/src/bgutil-ytdlp-pot-provider"
    paths = {
        "Base Folder": os.path.exists(base_path),
        "Server Folder": os.path.exists(f"{base_path}/server"),
        "Plugin Folder": os.path.exists(f"{base_path}/plugin"),
        "Extractor Script": os.path.exists(f"{base_path}/plugin/yt_dlp_plugins/extractor/getpot_bgutil.py")
    }
    return paths

# Iska result logs mein dekho. Agar sab 'True' hai, toh hum tayyar hain.
print(check_paths())
