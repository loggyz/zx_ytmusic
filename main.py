from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    # Poore project ki files ki list nikaal lega
    files_structure = []
    for root, dirs, files in os.walk(os.getcwd()):
        for name in dirs:
            if 'server' in name:
                files_structure.append(os.path.join(root, name))
    
    return jsonify({
        "current_working_directory": os.getcwd(),
        "found_server_paths": files_structure
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
