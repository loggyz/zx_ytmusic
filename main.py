"""
╔══════════════════════════════════════════════════════════════════╗
║  ZEROX HUB — MUSIC ENGINE BACKEND  v5.0                          ║
║  Flask API for Render deployment                                 ║
║  Endpoints: /search  /get_track  /normal  /vibe  /health         ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import re
import time
import random
import logging
import requests
import json
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
STREAM_TTL = 21600   # 6 hours — googlevideo URLs are valid ~6h


# ══════════════════════════════════════════════════════════════════
#  UTILS
# ══════════════════════════════════════════════════════════════════

def clean_name(text: str) -> str:
    """Strip YouTube noise from song/artist names."""
    if not text:
        return ""
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
        r"island|rca|epic\s*records|saregama|tips\s*music|speed\s*records|"
        r"white\s*hill|desi\s*music|venus|lahari|aditya\s*music)\b",
        " ", text, flags=re.I
    )
    text = re.sub(
        r"\b(slowed|reverb(ed)?|lofi|lo[\s\-]?fi|bass[\s\-]?boost(ed)?|"
        r"sped[\s\-]?up|nightcore|8d[\s\-]?audio)\b",
        " ", text, flags=re.I
    )
    text = re.sub(r"\bfeat\.?\s.*", " ", text, flags=re.I)
    text = re.sub(r"\bft\.?\s.*",   " ", text, flags=re.I)
    text = re.sub(r"\bprod\.?\s.*", " ", text, flags=re.I)
    text = re.sub(r"\s*-\s*topic\s*$", "", text, flags=re.I)
    text = re.sub(r"[-–—|]\s*$", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def best_thumb(thumbnails: list) -> str:
    """Return highest-resolution thumbnail URL."""
    if not thumbnails:
        return "https://i.imgur.com/8Q5FqWj.jpeg"
    def res(t):
        try:
            return int(t.get("width", 0)) * int(t.get("height", 0))
        except Exception:
            return 0
    sorted_thumbs = sorted(thumbnails, key=res, reverse=True)
    return sorted_thumbs[0].get("url", "https://i.imgur.com/8Q5FqWj.jpeg")


def safe_artist(track: dict) -> tuple[str, str | None]:
    """Extract (artist_name, browseId) from a YTMusic track dict."""
    artists = track.get("artists") or []
    if artists:
        a = artists[0]
        return a.get("name", "Unknown"), a.get("browseId")
    return "Unknown", None


def fmt_track(t: dict) -> dict:
    """Normalize a YTMusic track dict to our standard format."""
    a_name, a_id = safe_artist(t)
    album_obj    = t.get("album") or {}
    thumb_list   = (
        t.get("thumbnails")
        or t.get("thumbnail")
        or album_obj.get("thumbnails")
        or []
    )
    return {
        "title":     clean_name(t.get("title", "")),
        "artist":    clean_name(a_name),
        "artistId":  a_id,
        "videoId":   t.get("videoId", ""),
        "thumbnail": best_thumb(thumb_list),
        "duration":  t.get("duration", ""),
        "durationSecs": t.get("duration_seconds") or 0,
    }


# ══════════════════════════════════════════════════════════════════
#  STREAM EXTRACTION — INVIDIOUS + COBALT FALLBACK
# ══════════════════════════════════════════════════════════════════

def extract_m4a(video_id: str):
    video_id = video_id.strip()[:11]
    
    # Tier 1: Invidious Instances
    instances = [
        "https://inv.tux.rs",
        "https://invidious.projectsegfau.lt",
        "https://yewtu.be",
        "https://invidious.privacydev.net",
        "https://invidious.nerdvpn.de"
    ]
    random.shuffle(instances)
    
    for instance in instances:
        try:
            print(f"[Bypass] 🔄 Fetching from: {instance}", flush=True)
            api_url = f"{instance}/api/v1/videos/{video_id}"
            response = requests.get(api_url, timeout=6)
            
            if response.status_code == 200:
                data = response.json()
                adaptive_formats = data.get('adaptiveFormats', [])
                audio_url = next((f['url'] for f in adaptive_formats if str(f.get('itag')) == "140"), None)
                if not audio_url:
                    audio_url = next((f['url'] for f in adaptive_formats if "audio" in f.get('type', '')), None)
                
                if audio_url:
                    print(f"✅ Success! Link found via {instance}", flush=True)
                    return audio_url
        except Exception:
            continue

    # Tier 2: Cobalt API (Ultimate Fallback if Invidious fails)
    try:
        print("[Cobalt] 🔄 Trying Cobalt API as ultimate fallback...", flush=True)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "downloadMode": "audio"
        }
        cobalt_res = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=8)
        
        if cobalt_res.status_code == 200:
            print("✅ Success! Link found via Cobalt.", flush=True)
            return cobalt_res.json().get('url')
    except Exception as e:
        print(f"❌ Cobalt API failed: {str(e)[:50]}", flush=True)
            
    return None


# ══════════════════════════════════════════════════════════════════
#  ARTIST ENGINE — NORMAL MODE (Artist Chaining)
# ══════════════════════════════════════════════════════════════════

def get_artist_top_hits(artist_id: str | None, artist_name: str) -> tuple[list, dict]:
    tracks      = []
    artist_data = {}

    if artist_id:
        try:
            artist_data = yt.get_artist(artist_id)
            songs_section = artist_data.get("songs", {})
            results = songs_section.get("results", [])
            for t in results[:8]:
                vid = t.get("videoId")
                if vid:
                    tracks.append(fmt_track(t))
            if tracks:
                return tracks[:5], artist_data
        except Exception as e:
            log.warning(f"[artist] Artist page failed for {artist_name}: {e}")

    try:
        results = yt.search(f"{artist_name} popular songs", filter="songs")
        for t in results[:8]:
            vid = t.get("videoId")
            if vid:
                tracks.append(fmt_track(t))
    except Exception as e:
        log.warning(f"[artist] Search fallback failed: {e}")

    return tracks[:5], artist_data


def find_next_artist(artist_data: dict, current_video_id: str, artist_history: set) -> tuple[str, str | None, str | None]:
    related = artist_data.get("related", {}).get("results", [])
    for r in related:
        name = r.get("title", "")
        if name and name not in artist_history:
            return name, r.get("browseId"), None

    try:
        radio = yt.get_watch_playlist(current_video_id, limit=50)
        for rt in radio.get("tracks", []):
            arts = rt.get("artists", [])
            if arts:
                name = arts[0].get("name", "")
                if name and name not in artist_history:
                    return name, arts[0].get("browseId"), rt.get("videoId")
    except Exception:
        pass

    emergency_queries = ["Indian Indie hits", "Bollywood underground", "Global viral songs", "Trending new artists"]
    random.shuffle(emergency_queries)
    for q in emergency_queries:
        try:
            results = yt.search(q, filter="songs")
            for t in results:
                arts = t.get("artists", [])
                if arts:
                    name = arts[0].get("name", "")
                    if name and name not in artist_history:
                        return name, arts[0].get("browseId"), t.get("videoId")
        except Exception:
            continue

    return "", None, None


# ══════════════════════════════════════════════════════════════════
#  VIBE ENGINE — SHUFFLE / DISCOVERY MODE
# ══════════════════════════════════════════════════════════════════

def get_vibe_batch(video_id: str, history: set, limit: int = 8) -> list:
    try:
        playlist = yt.get_watch_playlist(video_id, limit=limit + 5)
        tracks   = []
        for t in playlist.get("tracks", [])[1:]:
            tid = t.get("videoId")
            if tid and tid not in history:
                tracks.append(fmt_track(t))
                if len(tracks) >= limit:
                    break
        return tracks
    except Exception as e:
        log.warning(f"[vibe] Failed for {video_id}: {e}")
        return []


# ══════════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ══════════════════════════════════════════════════════════════════

# HEALTH CHECKS - Render needs this on both '/' and '/health'
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "5.0", "engine": "ZeroX Hub"}), 200

# EXTRACTION ROUTE
@app.route('/get_track', methods=["GET"])
def get_track():
    v_id = request.args.get('id')
    if not v_id:
        return jsonify({"error": "No ID provided"}), 400
        
    link = extract_m4a(v_id)
    if link:
        return jsonify({"url": link})
    return jsonify({"error": "Extraction failed on all instances"}), 500

# SEARCH ROUTE
@app.route("/search", methods=["GET"])
def search():
    q = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 10)), 30)
    if not q:
        return jsonify({"error": "Missing query parameter 'q'"}), 400
    try:
        results = yt.search(q, filter="songs")
        tracks  = [fmt_track(t) for t in results[:limit] if t.get("videoId")]
        return jsonify({"query": q, "results": tracks}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# NORMAL MODE ROUTE
@app.route("/normal", methods=["GET"])
def normal():
    artist_id   = request.args.get("artist_id", "").strip() or None
    artist_name = request.args.get("artist_name", "").strip()
    backup_vid  = request.args.get("id", "").strip()
    history_raw = request.args.get("history", "")
    artist_hist_raw = request.args.get("artist_history", "")

    if not artist_name and not artist_id:
        return jsonify({"error": "Provide 'artist_name' or 'artist_id'"}), 400

    history        = set(h.strip() for h in history_raw.split(",")     if h.strip())
    artist_history = set(h.strip() for h in artist_hist_raw.split(",") if h.strip())
    artist_history.add(artist_name)

    tracks, artist_data = get_artist_top_hits(artist_id, artist_name)
    fresh_tracks = [t for t in tracks if t["videoId"] not in history]
    chain_vid     = backup_vid or (tracks[0]["videoId"] if tracks else "")
    next_name, next_id, next_vid = find_next_artist(artist_data, chain_vid, artist_history)

    return jsonify({
        "artist":  {"name": artist_name, "artistId": artist_id},
        "tracks":  fresh_tracks,
        "nextArtist": {"name": next_name, "artistId": next_id, "videoId":  next_vid or chain_vid},
    }), 200

# VIBE MODE ROUTE
@app.route("/vibe", methods=["GET"])
def vibe():
    vid         = request.args.get("id", "").strip()
    limit       = min(int(request.args.get("limit", 8)), 20)
    history_raw = request.args.get("history", "")

    if not vid:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    history = set(h.strip() for h in history_raw.split(",") if h.strip())
    tracks  = get_vibe_batch(vid, history, limit)

    if not tracks:
        for eq in ["trending songs", "viral hits", "top songs 2025"]:
            try:
                results = yt.search(eq, filter="songs")
                for t in results:
                    if t.get("videoId") and t["videoId"] not in history:
                        tracks.append(fmt_track(t))
                    if len(tracks) >= limit:
                        break
                if tracks:
                    break
            except Exception:
                continue

    return jsonify({"seedId": vid, "tracks": tracks}), 200

@app.route("/similar_artist", methods=["GET"])
def similar_artist():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"error": "Missing 'name' parameter"}), 400
    try:
        results = yt.search(name, filter="artists")
        if not results:
            return jsonify({"artists": []}), 200
        artist_data = yt.get_artist(results[0].get("browseId")) if results[0].get("browseId") else {}
        related = artist_data.get("related", {}).get("results", [])[:5]
        return jsonify({"query": name, "artists": [{"name": r.get("title", ""), "artistId": r.get("browseId")} for r in related]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/batch_streams", methods=["POST"])
def batch_streams():
    data = request.get_json(force=True, silent=True) or {}
    ids  = data.get("ids", [])
    if not ids or not isinstance(ids, list):
        return jsonify({"error": "Provide 'ids' list"}), 400
    
    results = []
    for vid in ids[:5]:
        url = extract_m4a(vid)
        results.append({"videoId": vid, "streamUrl": url} if url else {"videoId": vid, "error": "extraction_failed"})

    return jsonify({"results": results}), 200

# ══════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "available": [
        "/health", "/search", "/get_track", "/normal", "/vibe", "/similar_artist", "/batch_streams"
    ]}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    log.info(f"🚀 ZeroX Hub Backend v5.0 starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
