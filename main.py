import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    # Render ke internal paths check karne ke liye logic
    base_path = "/opt/render/project/src/bgutil-ytdlp-pot-provider"
    
    report = {
        "status": "Checking Paths...",
        "exists_base_folder": os.path.exists(base_path),
        "exists_server_folder": os.path.exists(f"{base_path}/server"),
        "exists_plugin_folder": os.path.exists(f"{base_path}/plugin"),
        "exists_extractor": os.path.exists(f"{base_path}/plugin/yt_dlp_plugins/extractor/getpot_bgutil.py"),
        "current_directory_files": os.listdir('/opt/render/project/src/')
    }
    return jsonify(report)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
