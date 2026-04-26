"""
╔══════════════════════════════════════════════════════════════════╗
║  ZEROX HUB — MUSIC ENGINE BACKEND  v5.1 (Proxy Edition)         ║
║  Flask API for Render deployment                                  ║
║  Endpoints: /search  /get_track  /normal  /vibe  /health        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import re
import time
import random
import logging
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

# ─── PROXY LIST ──────────────────────────────────────────────────
# Ye saari proxies request ko Render se bypass karke jayengi
PROXY_LIST = [
    "http://purevpn0s12153504:1LTpwxbCJbEdXo@px022505.pointtoserver.com:10780",
    "http://purevpn0s12153504:1LTpwxbCJbEdXo@px460101.pointtoserver.com:10780",
    "http://g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2@au-per.pvdata.host:8080",
    "http://g2rTXpNfPdcw2fzGtWKp62yH:nizar1elad2@ph-man.pvdata.host:8080",
    "http://socialwire:87xb2kziRk4xa@153.121.71.115:822"
]

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
#  STREAM EXTRACTION — FORMAT 140 WITH PROXY ROTATION
# ══════════════════════════════════════════════════════════════════

def extract_m4a(video_id: str):
    log.info(f"[stream] 🔄 Global Extraction Start: {video_id}")
    
    video_id = video_id.strip()[:11]
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Proxies ko shuffle kar rahe hain har request pe
    active_proxies = list(PROXY_LIST)
    random.shuffle(active_proxies)

    for i, proxy in enumerate(active_proxies):
        safe_log = proxy.split('@')[-1] if '@' in proxy else "Proxy"
        log.info(f"[Attempt {i+1}] Testing via: {safe_log}")

        ydl_opts = {
            'format': '140/bestaudio',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'proxy': proxy,
            'socket_timeout': 15, # Connection time limit
            'retries': 2,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android'], # Desktop block ho jata hai jaldi
                    'skip': ['webpage', 'configs']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Sec-Fetch-Mode': 'navigate'
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Meta-data fetch karo bina download kiye
                info = ydl.extract_info(url, download=False)
                stream_url = info.get('url')
                
                if stream_url:
                    log.info(f"✅ Extraction SUCCESS via {safe_log}")
                    return stream_url
        except Exception as e:
            err_msg = str(e).lower()
            if "403" in err_msg:
                log.error(f"❌ Proxy {safe_log} is Blocked (403 Forbidden)")
            elif "timeout" in err_msg:
                log.error(f"❌ Proxy {safe_log} Timed Out")
            else:
                log.error(f"❌ Proxy Error: {str(e)[:60]}")
            
            # Agar last proxy nahi hai toh thoda gap deke agali try karo
            if i < len(active_proxies) - 1:
                time.sleep(1) 
            continue

    log.error(f"🔥 Critical: All {len(active_proxies)} proxies failed for {video_id}")
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
                log.info(f"[artist] ✅ Got {len(tracks)} tracks for {artist_name} from artist page")
                return tracks[:5], artist_data
        except Exception as e:
            log.warning(f"[artist] Artist page failed for {artist_name}: {e}")

    try:
        results = yt.search(f"{artist_name} popular songs", filter="songs")
        for t in results[:8]:
            vid = t.get("videoId")
            if vid:
                tracks.append(fmt_track(t))
        log.info(f"[artist] 🔍 Search fallback: {len(tracks)} tracks for {artist_name}")
    except Exception as e:
        log.warning(f"[artist] Search fallback failed: {e}")

    return tracks[:5], artist_data


def find_next_artist(
    artist_data: dict,
    current_video_id: str,
    artist_history: set,
) -> tuple[str, str | None, str | None]:

    related = artist_data.get("related", {}).get("results", [])
    for r in related:
        name = r.get("title", "")
        if name and name not in artist_history:
            log.info(f"[chain] ✅ Related artist: {name}")
            return name, r.get("browseId"), None

    try:
        radio = yt.get_watch_playlist(current_video_id, limit=50)
        for rt in radio.get("tracks", []):
            arts = rt.get("artists", [])
            if arts:
                name = arts[0].get("name", "")
                if name and name not in artist_history:
                    log.info(f"[chain] 🔁 Radio found artist: {name}")
                    return name, arts[0].get("browseId"), rt.get("videoId")
    except Exception as e:
        log.warning(f"[chain] Radio scan failed: {e}")

    emergency_queries = [
        "Indian Indie hits",
        "Bollywood underground",
        "Global viral songs",
        "International pop hits",
        "Trending new artists",
    ]
    random.shuffle(emergency_queries)
    for q in emergency_queries:
        try:
            results = yt.search(q, filter="songs")
            for t in results:
                arts = t.get("artists", [])
                if arts:
                    name = arts[0].get("name", "")
                    if name and name not in artist_history:
                        log.info(f"[chain] 🚀 Emergency jump → {name} (query: {q})")
                        return name, arts[0].get("browseId"), t.get("videoId")
        except Exception:
            continue

    log.warning("[chain] ⚠️ All chain methods exhausted")
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
        log.info(f"[vibe] ✅ Got {len(tracks)} vibe tracks for seed {video_id}")
        return tracks
    except Exception as e:
        log.warning(f"[vibe] Failed for {video_id}: {e}")
        return []


# ══════════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "5.1", "engine": "ZeroX Hub Proxy Edition"}), 200

@app.route("/search", methods=["GET"])
def search():
    q     = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 10)), 30)

    if not q:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    try:
        results = yt.search(q, filter="songs")
        tracks  = [fmt_track(t) for t in results[:limit] if t.get("videoId")]
        log.info(f"[search] '{q}' → {len(tracks)} results")
        return jsonify({"query": q, "results": tracks}), 200
    except Exception as e:
        log.error(f"[search] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/get_track', methods=['GET'])
def get_track():
    video_id = request.args.get('id')
    if not video_id:
        return jsonify({"error": "No ID provided"}), 400
    
    video_id = video_id.strip()
    
    url = extract_m4a(video_id)
    if url:
        return jsonify({"streamUrl": url, "videoId": video_id})
    return jsonify({"error": "All proxy stream extractions failed"}), 502

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

    log.info(f"[normal] '{artist_name}' → {len(fresh_tracks)} tracks | next: '{next_name}'")

    return jsonify({
        "artist":  {"name": artist_name, "artistId": artist_id},
        "tracks":  fresh_tracks,
        "nextArtist": {
            "name":     next_name,
            "artistId": next_id,
            "videoId":  next_vid or chain_vid,
        },
    }), 200

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
        emergency_queries = ["trending songs", "viral hits", "top songs 2026"]
        for eq in emergency_queries:
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
        artist_id = results[0].get("browseId")
        artist_data = {}
        if artist_id:
            artist_data = yt.get_artist(artist_id)
        related = artist_data.get("related", {}).get("results", [])[:5]
        artists = [{"name": r.get("title", ""), "artistId": r.get("browseId")} for r in related]
        return jsonify({"query": name, "artists": artists}), 200
    except Exception as e:
        log.error(f"[similar_artist] {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/batch_streams", methods=["POST"])
def batch_streams():
    data = request.get_json(force=True, silent=True) or {}
    ids  = data.get("ids", [])
    if not ids or not isinstance(ids, list):
        return jsonify({"error": "Provide 'ids' list"}), 400
    ids = ids[:5]

    results = []
    for vid in ids:
        url = extract_m4a(vid)
        if url:
            results.append({"videoId": vid, "streamUrl": url})
        else:
            results.append({"videoId": vid, "error": "extraction_failed"})

    return jsonify({"results": results}), 200

# ══════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found", "available": [
        "/health", "/search", "/get_track", "/normal", "/vibe",
        "/similar_artist", "/batch_streams",
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
    log.info(f"🚀 ZeroX Hub Backend v5.1 (Proxy Engine) starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
