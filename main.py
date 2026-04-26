"""
╔══════════════════════════════════════════════════════════════════╗
║  ZEROX HUB — MUSIC ENGINE BACKEND  v5.0                         ║
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
    # Remove bracket content
    text = re.sub(r"\[.*?\]", " ", text)
    text = re.sub(r"\(.*?\)", " ", text)
    # Quality/format tags
    text = re.sub(r"\b(4k|8k|hd|hq|uhd|fhd|1080p|720p|480p)\b", " ", text, flags=re.I)
    # Marketing junk
    text = re.sub(
        r"\b(official\s*(music\s*)?video|official\s*audio|lyric\s*video|"
        r"lyrics?|visualizer|audio\s*song|full\s*song|full\s*version|"
        r"title\s*track|title\s*song|new\s*song|latest\s*song)\b",
        " ", text, flags=re.I
    )
    # Record labels
    text = re.sub(
        r"\b(t[\s\-]?series|zee\s*music|sony\s*music|eros\s*now|warner|"
        r"universal|atlantic|columbia|republic|interscope|def\s*jam|"
        r"island|rca|epic\s*records|saregama|tips\s*music|speed\s*records|"
        r"white\s*hill|desi\s*music|venus|lahari|aditya\s*music)\b",
        " ", text, flags=re.I
    )
    # Audio effects
    text = re.sub(
        r"\b(slowed|reverb(ed)?|lofi|lo[\s\-]?fi|bass[\s\-]?boost(ed)?|"
        r"sped[\s\-]?up|nightcore|8d[\s\-]?audio)\b",
        " ", text, flags=re.I
    )
    # Feat / prod
    text = re.sub(r"\bfeat\.?\s.*", " ", text, flags=re.I)
    text = re.sub(r"\bft\.?\s.*",   " ", text, flags=re.I)
    text = re.sub(r"\bprod\.?\s.*", " ", text, flags=re.I)
    # Topic suffix from channel names
    text = re.sub(r"\s*-\s*topic\s*$", "", text, flags=re.I)
    # Clean trailing dash / pipe junk
    text = re.sub(r"[-–—|]\s*$", "", text)
    # Collapse whitespace
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def best_thumb(thumbnails: list) -> str:
    """Return highest-resolution thumbnail URL."""
    if not thumbnails:
        return "https://i.imgur.com/8Q5FqWj.jpeg"
    # Sort by resolution descending (width * height)
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
#  STREAM EXTRACTION — FORMAT 140 (M4A 128kbps)
# ══════════════════════════════════════════════════════════════════

import os
def extract_m4a(video_id: str):
    video_id = video_id.strip()[:11]
    cookie_file = "/tmp/cookies.txt" 
    
    cookie_data = os.environ.get('YT_COOKIES')
    if cookie_data:
        with open(cookie_file, "w") as f:
            f.write(cookie_data)
    
    ydl_opts = {
        # '140' m4a hai, agar wo na mile toh koi bhi best audio utha lo
        'format': '140/bestaudio/best', 
        'quiet': False,
        'no_warnings': False,
        'nocheckcertificate': True,
        'cookiefile': cookie_file if os.path.exists(cookie_file) else None,
        
        'extractor_args': {
            'youtube': {
                # 'mweb' aur 'android' ka combo sabse best hai formats ke liye
                'player_client': ['mweb', 'android'],
                'player_skip': [] 
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
        }
    }

    url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[Stream] 🔄 Target format 140 or best for {video_id}", flush=True)
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url')
            
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
                
            if stream_url:
                print(f"✅ Success! URL found.", flush=True)
                return stream_url
                
    except Exception as e:
        print(f"❌ Final Extraction Error: {str(e)[:200]}", flush=True)
        if os.path.exists(cookie_file):
            os.remove(cookie_file)
            
    return None



# ══════════════════════════════════════════════════════════════════
#  ARTIST ENGINE — NORMAL MODE (Artist Chaining)
# ══════════════════════════════════════════════════════════════════

def get_artist_top_hits(artist_id: str | None, artist_name: str) -> tuple[list, dict]:
    """
    Return (top_5_tracks, artist_data_dict).
    Fetches from YTMusic artist page; falls back to search.
    """
    tracks      = []
    artist_data = {}

    # Path 1: Artist page → songs
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

    # Path 2: Search fallback
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
    """
    Chain to next related artist using 3-tier fallback.
    Returns (artist_name, artist_id, video_id_hint).
    """

    # Tier 1: Related artists from artist page
    related = artist_data.get("related", {}).get("results", [])
    for r in related:
        name = r.get("title", "")
        if name and name not in artist_history:
            log.info(f"[chain] ✅ Related artist: {name}")
            return name, r.get("browseId"), None

    # Tier 2: Radio playlist scan
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

    # Tier 3: Emergency jump (Loop Breaker)
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
    """
    Return a batch of similar tracks via watch playlist (radio).
    Filters out already-played video IDs.
    """
    try:
        playlist = yt.get_watch_playlist(video_id, limit=limit + 5)
        tracks   = []
        for t in playlist.get("tracks", [])[1:]:  # skip seed track
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
    """Health check — Render pings this to keep the instance warm."""
    return jsonify({"status": "ok", "version": "5.0", "engine": "ZeroX Hub"}), 200


@app.route("/search", methods=["GET"])
def search():
    """
    GET /search?q=QUERY&limit=10
    Search YTMusic for songs.
    Returns list of {title, artist, artistId, videoId, thumbnail, duration}.
    """
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
    print(f"DEBUG: Received ID -> {video_id}") # Ye line logs laane ke liye zaroori hai
    if not video_id:
        return jsonify({"error": "No ID provided"}), 400
    
    # ID ko strictly clean karo
    video_id = video_id.strip()
    
    url = extract_m4a(video_id)
    if url:
        return jsonify({"streamUrl": url, "videoId": video_id})
    return jsonify({"error": "Stream extraction failed"}), 502


@app.route("/normal", methods=["GET"])
def normal():
    """
    GET /normal?artist_id=ID&artist_name=NAME&id=VIDEO_ID&history=id1,id2,...
    Normal mode: returns current artist's top 5 tracks + next artist info.
    Returns {tracks, nextArtist: {name, artistId, videoId}}.
    """
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

    # Filter already-played
    fresh_tracks = [t for t in tracks if t["videoId"] not in history]

    # Find next artist for chaining
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
    """
    GET /vibe?id=VIDEO_ID&limit=8&history=id1,id2,...
    Shuffle/Discovery mode: returns similar tracks via YTMusic watch playlist.
    Returns {seedId, tracks}.
    """
    vid         = request.args.get("id", "").strip()
    limit       = min(int(request.args.get("limit", 8)), 20)
    history_raw = request.args.get("history", "")

    if not vid:
        return jsonify({"error": "Missing 'id' parameter"}), 400

    history = set(h.strip() for h in history_raw.split(",") if h.strip())
    tracks  = get_vibe_batch(vid, history, limit)

    # Emergency fallback if empty
    if not tracks:
        emergency_queries = ["trending songs", "viral hits", "top songs 2025"]
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
    """
    GET /similar_artist?name=ARTIST_NAME
    Returns up to 5 similar artists with their top track info.
    """
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
    """
    POST /batch_streams
    Body: {"ids": ["vid1", "vid2", ...]}
    Resolve multiple stream URLs in one request (for JIT prefetch).
    Returns {results: [{videoId, streamUrl, error?}, ...]}.
    """
    data = request.get_json(force=True, silent=True) or {}
    ids  = data.get("ids", [])
    if not ids or not isinstance(ids, list):
        return jsonify({"error": "Provide 'ids' list"}), 400
    ids = ids[:5]   # Hard cap — don't overload

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
    log.info(f"🚀 ZeroX Hub Backend v5.0 starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
