"""
╔══════════════════════════════════════════════════════════════════╗
║  ZEROX HUB — MUSIC ENGINE BACKEND  v5.1 (HF Optimized)          ║
║  Flask API for Hugging Face Deployment                            ║
║  Endpoints: /search  /get_track  /normal  /vibe  /health        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import re
import time
import random
import logging
import tempfile
from functools import lru_cache

from flask import Flask, jsonify, request
from flask_cors import CORS
import yt_dlp
from ytmusicapi import YTMusic

# ─── App Init ────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins="*")

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

yt = YTMusic()

# ─── In-memory caches ────────────────────────────────────────────
_stream_cache: dict[str, dict] = {}   # video_id → {url, expires}
_meta_cache:   dict[str, dict] = {}   # video_id → metadata
STREAM_TTL = 21600   # 6 hours

# ══════════════════════════════════════════════════════════════════
#  UTILS
# ══════════════════════════════════════════════════════════════════

def clean_name(text: str) -> str:
    """Strip YouTube noise from song/artist names."""
    if not text: return ""
    text = re.sub(r"\[.*?\]", " ", text)
    text = re.sub(r"\(.*?\)", " ", text)
    text = re.sub(r"\b(4k|8k|hd|hq|uhd|fhd|1080p|720p|480p)\b", " ", text, flags=re.I)
    text = re.sub(
        r"\b(official\s*(music\s*)?video|official\s*audio|lyric\s*video|"
        r"lyrics?|visualizer|audio\s*song|full\s*song|full\s*version|"
        r"title\s*track|title\s*song|new\s*song|latest\s*song)\b",
        " ", text, flags=re.I
    )
    text = re.sub(
        r"\b(t[\s\-]?series|zee\s*music|sony\s*music|eros\s*now|warner|"
        r"universal|atlantic|columbia|republic|interscope|def\s*jam|"
        r"island|rca|epic\s*records|saregama|tips\s*music|speed\s*records)\b",
        " ", text, flags=re.I
    )
    text = re.sub(r"\b(slowed|reverb(ed)?|lofi|lo[\s\-]?fi|bass[\s\-]?boost(ed)?|sped[\s\-]?up|nightcore|8d[\s\-]?audio)\b", " ", text, flags=re.I)
    text = re.sub(r"\bfeat\.?\s.*|\bft\.?\s.*|\bprod\.?\s.*", " ", text, flags=re.I)
    text = re.sub(r"\s*-\s*topic\s*$", "", text, flags=re.I)
    text = re.sub(r"[-–—|]\s*$", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text

def best_thumb(thumbnails: list) -> str:
    if not thumbnails: return "https://i.imgur.com/8Q5FqWj.jpeg"
    def res(t):
        try: return int(t.get("width", 0)) * int(t.get("height", 0))
        except: return 0
    sorted_thumbs = sorted(thumbnails, key=res, reverse=True)
    return sorted_thumbs[0].get("url", "https://i.imgur.com/8Q5FqWj.jpeg")

def safe_artist(track: dict) -> tuple[str, str | None]:
    artists = track.get("artists") or []
    if artists:
        a = artists[0]
        return a.get("name", "Unknown"), a.get("browseId")
    return "Unknown", None

def fmt_track(t: dict) -> dict:
    a_name, a_id = safe_artist(t)
    album_obj = t.get("album") or {}
    thumb_list = t.get("thumbnails") or t.get("thumbnail") or album_obj.get("thumbnails") or []
    return {
        "title": clean_name(t.get("title", "")),
        "artist": clean_name(a_name),
        "artistId": a_id,
        "videoId": t.get("videoId", ""),
        "thumbnail": best_thumb(thumb_list),
        "duration": t.get("duration", ""),
        "durationSecs": t.get("duration_seconds") or 0,
    }

# ══════════════════════════════════════════════════════════════════
#  STREAM EXTRACTION (HF & COOKIE OPTIMIZED)
# ══════════════════════════════════════════════════════════════════

def extract_m4a(video_id: str):
    video_id = video_id.strip()[:11]
    log.info(f"[stream] 🔄 Extraction started: {video_id}")
    
    cookie_data = os.environ.get('YT_COOKIES')
    cookie_path = None
    if cookie_data:
        fd, cookie_path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(cookie_data)

    ydl_opts = {
        'format': '140/bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'cookiefile': cookie_path,
        'source_address': '0.0.0.0',
        'extractor_args': {'youtube': {'player_client': ['android', 'ios'], 'player_skip': ['webpage', 'configs']}},
        'http_headers': {'User-Agent': 'com.google.android.youtube/19.10.35 (Linux; U; Android 11)'}
    }
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url')
            if stream_url:
                log.info(f"[stream] ✅ Success: {video_id}")
                return stream_url
    except Exception as e:
        log.error(f"[stream] ❌ Failed: {str(e)[:50]}")
    finally:
        if cookie_path and os.path.exists(cookie_path):
            try: os.remove(cookie_path)
            except: pass
    return None

# ══════════════════════════════════════════════════════════════════
#  ARTIST ENGINE & VIBE ENGINE
# ══════════════════════════════════════════════════════════════════

def get_artist_top_hits(artist_id, artist_name):
    tracks, artist_data = [], {}
    if artist_id:
        try:
            artist_data = yt.get_artist(artist_id)
            results = artist_data.get("songs", {}).get("results", [])
            tracks = [fmt_track(t) for t in results[:8] if t.get("videoId")]
            if tracks: return tracks[:5], artist_data
        except: pass
    try:
        results = yt.search(f"{artist_name} popular songs", filter="songs")
        tracks = [fmt_track(t) for t in results[:8] if t.get("videoId")]
    except: pass
    return tracks[:5], artist_data

def find_next_artist(artist_data, current_vid, artist_history):
    related = artist_data.get("related", {}).get("results", [])
    for r in related:
        name = r.get("title", "")
        if name and name not in artist_history:
            return name, r.get("browseId"), None
    try:
        radio = yt.get_watch_playlist(current_vid, limit=20)
        for rt in radio.get("tracks", []):
            arts = rt.get("artists", [])
            if arts and arts[0].get("name") not in artist_history:
                return arts[0].get("name"), arts[0].get("browseId"), rt.get("videoId")
    except: pass
    return "Trending Artist", None, None

def get_vibe_batch(video_id, history, limit=8):
    try:
        playlist = yt.get_watch_playlist(video_id, limit=limit + 5)
        return [fmt_track(t) for t in playlist.get("tracks", [])[1:] if t.get("videoId") not in history][:limit]
    except: return []

# ══════════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": "5.1-HF", "engine": "ZeroX Hub"}), 200

@app.route("/search")
def search():
    q = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 10)), 30)
    if not q: return jsonify({"error": "Missing query"}), 400
    try:
        results = yt.search(q, filter="songs")
        tracks = [fmt_track(t) for t in results[:limit] if t.get("videoId")]
        return jsonify({"query": q, "results": tracks}), 200
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/get_track')
def get_track():
    vid = request.args.get('id')
    if not vid: return jsonify({"error": "No ID"}), 400
    url = extract_m4a(vid)
    if url: return jsonify({"streamUrl": url, "videoId": vid})
    return jsonify({"error": "Failed"}), 502

@app.route("/normal")
def normal():
    artist_id = request.args.get("artist_id", "").strip() or None
    artist_name = request.args.get("artist_name", "").strip()
    backup_vid = request.args.get("id", "").strip()
    history = set(request.args.get("history", "").split(","))
    artist_history = set(request.args.get("artist_history", "").split(","))
    artist_history.add(artist_name)

    tracks, artist_data = get_artist_top_hits(artist_id, artist_name)
    fresh_tracks = [t for t in tracks if t["videoId"] not in history]
    
    chain_vid = backup_vid or (tracks[0]["videoId"] if tracks else "")
    next_name, next_id, next_vid = find_next_artist(artist_data, chain_vid, artist_history)

    return jsonify({
        "artist": {"name": artist_name, "artistId": artist_id},
        "tracks": fresh_tracks,
        "nextArtist": {"name": next_name, "artistId": next_id, "videoId": next_vid or chain_vid}
    }), 200

@app.route("/vibe")
def vibe():
    vid = request.args.get("id", "").strip()
    limit = min(int(request.args.get("limit", 8)), 20)
    history = set(request.args.get("history", "").split(","))
    tracks = get_vibe_batch(vid, history, limit)
    return jsonify({"seedId": vid, "tracks": tracks}), 200

@app.route("/batch_streams", methods=["POST"])
def batch_streams():
    data = request.get_json(force=True, silent=True) or {}
    ids = data.get("ids", [])[:5]
    results = []
    for vid in ids:
        url = extract_m4a(vid)
        results.append({"videoId": vid, "streamUrl": url} if url else {"videoId": vid, "error": "failed"})
    return jsonify({"results": results}), 200

# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # HF Spaces use 7860
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port)
