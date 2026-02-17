"""
Persistence for user film data so we don't re-scrape everything on refresh.

All caching and persistence live in /tmp by default (nothing in data/).
- Dir: CINEPHILES_DATA_DIR (default: /tmp). One JSON per user: {dir}/stats_{username}.json
- Shape: { "username": { "films": { "slug": { ... } }, "stats": { ... } } }
- Durable source of truth is the FilmLog sheet; /tmp is ephemeral across restarts.
"""

import os
import json
import glob

DATA_DIR = os.environ.get("CINEPHILES_DATA_DIR", "/tmp")


def _user_file(username):
    return os.path.join(DATA_DIR, f"stats_{username}.json")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_user_films(username):
    """Load persisted film data for a user. Returns dict with keys 'username', 'films', 'stats' (or empty)."""
    ensure_data_dir()
    path = _user_file(username)
    if not os.path.exists(path):
        return {username: {"films": {}, "stats": {}}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {username: {"films": {}, "stats": {}}}
    if username not in data:
        data[username] = {"films": {}, "stats": {}}
    data[username].setdefault("films", {})
    data[username].setdefault("stats", {})
    return data


def save_user_films(username, data):
    """Save film data for a user. data = { username: { 'films': {...}, 'stats': {...} } } or { 'films': {...}, 'stats': {...} }."""
    ensure_data_dir()
    path = _user_file(username)
    if isinstance(data, dict) and username in data:
        blob = data
    else:
        blob = {username: {"films": data.get("films", {}), "stats": data.get("stats", {})}}
    blob.setdefault(username, {})
    blob[username].setdefault("films", {})
    blob[username].setdefault("stats", {})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(blob, f, indent=2)


def load_all_users_films():
    """Load all per-user stats files into one combined dict (same shape as load_all_stats_caches_in_memory)."""
    ensure_data_dir()
    pattern = os.path.join(DATA_DIR, "stats_*.json")
    combined = {}
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for user, user_data in data.items():
            if user in combined and isinstance(user_data, dict) and isinstance(combined[user], dict):
                combined[user].setdefault("films", {}).update(user_data.get("films", {}))
                combined[user].setdefault("stats", {}).update(user_data.get("stats", {}))
            else:
                combined[user] = user_data if isinstance(user_data, dict) else {"films": {}, "stats": {}}
    return combined
