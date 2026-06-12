from typing import Optional, Dict
import time
import requests
from config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_IMAGE_BASE

_cache: Dict[str, Dict] = {}
_cache_expiry: Dict[str, float] = {}
TTL_SECONDS = 60 * 60 * 24  

def _get_cached(key: str) -> Optional[Dict]:
    now = time.time()
    if key in _cache and _cache_expiry.get(key, 0) > now:
        return _cache[key]
    return None

def _set_cached(key: str, value: Dict) -> None:
    _cache[key] = value
    _cache_expiry[key] = time.time() + TTL_SECONDS

def search_movie(title: str) -> Optional[Dict]:
    """
    Returns dict with poster_url, overview, release_date, tmdb_id
    """
    if not TMDB_API_KEY:
        return None

    key = f"search:{title.lower().strip()}"
    cached = _get_cached(key)
    if cached is not None:
        return cached

    params = {"api_key": TMDB_API_KEY, "query": title}
    resp = requests.get(f"{TMDB_BASE_URL}/search/movie", params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results", [])
    if not results:
        _set_cached(key, {})
        return {}

    top = results[0]
    poster_path = top.get("poster_path")
    poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

    info = {
        "tmdb_id": top.get("id"),
        "poster_url": poster_url,
        "overview": top.get("overview"),
        "release_date": top.get("release_date"),
    }
    _set_cached(key, info)
    return info