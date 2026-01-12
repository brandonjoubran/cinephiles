import os, time, json, glob

CACHE_FILE = "/tmp/stats_cache.json"
CACHE_TTL = 60 * 60 * 12  # 12 hours
CACHE_PATH = "/tmp/"

def is_cache_valid():
    return os.path.exists(CACHE_FILE) and (time.time() - os.path.getmtime(CACHE_FILE) < CACHE_TTL)

def load_cache():
    with open(CACHE_FILE, 'r') as f:
        return json.load(f)

def save_cache(data):
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def flush_cache():
    if os.path.exists(CACHE_FILE):  # Check if the cache file exists
        os.remove(CACHE_FILE) 

def update_film_cache(username, film_data):
    cache = load_cache()
    cache.setdefault(username, {}).setdefault("films", {})
    for key, value in film_data.items():
        print(f"Updating cache for {username}: {key} {value}")
        cache[username]["films"][key] = value
    save_cache(cache)

def ensure_cache_file(username):
    """Create the cache file (and parent dir) if it doesn't exist, with an empty JSON object."""
    CACHE_FILE = f"/tmp/stats_{username}_cache.json"
    dirpath = os.path.dirname(CACHE_FILE) or "/"
    try:
        if dirpath and not os.path.exists(dirpath):
            os.makedirs(dirpath, exist_ok=True)
        if not os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f)
    except Exception as e:
        print(f"⚠️ Failed to ensure cache file: {e}")

def load_stats_cache(username):
    ensure_cache_file(username)
    CACHE_FILE = f"/tmp/stats_{username}_cache.json"
    with open(CACHE_FILE, 'r') as f:
        return json.load(f)

def save_stats_cache(username, data):
    CACHE_FILE = f"/tmp/stats_{username}_cache.json"
    print(f"Saving stats cache for {username}: {data}")
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def flush_stats_cache(username):
    CACHE_FILE = f"/tmp/stats_{username}_cache.json"
    if os.path.exists(CACHE_FILE):  # Check if the cache file exists
        os.remove(CACHE_FILE) 

def load_all_stats_caches_in_memory(dirpath=None, pattern="stats_*_cache.json"):
    """
    Read all per-user stats cache files in `dirpath` (defaults to CACHE_PATH)
    and return a single combined dict (keeps everything in memory; does not write files).
    Merges nested dicts for username -> films safely.
    """
    dirpath = dirpath or CACHE_PATH
    files = glob.glob(os.path.join(dirpath, pattern))
    combined = {}
    # print(files)
    for path in sorted(files):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        if not isinstance(data, dict):
            # store non-dict payloads under filename to avoid data loss
            combined.setdefault("_files", {})[os.path.basename(path)] = data
            continue
        for user, user_data in data.items():
            if user not in combined:
                combined[user] = user_data if isinstance(user_data, dict) else user_data
                continue
            # both exist and are dicts -> merge shallowly, deeper merge for nested dicts
            if isinstance(user_data, dict) and isinstance(combined[user], dict):
                for k, v in user_data.items():
                    if isinstance(v, dict) and isinstance(combined[user].get(k), dict):
                        combined[user][k].update(v)
                    else:
                        combined[user][k] = v
            else:
                combined[user] = user_data
    return combined

# print(load_all_stats_caches_in_memory())