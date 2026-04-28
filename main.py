from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    # Ye poore project ki har ek file aur folder ki list bana dega
    all_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        # Hum sirf 3 level tak deep jayenge taaki list bahut lambi na ho
        level = root.replace(os.getcwd(), '').count(os.sep)
        if level <= 2:
            all_files.append(f"Folder: {root}")
            for f in files:
                all_files.append(f"  -- File: {f}")
    
    return jsonify({
        "current_directory": os.getcwd(),
        "project_structure": all_files
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
