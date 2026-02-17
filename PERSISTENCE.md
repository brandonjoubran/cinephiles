# Persistence for film data

So you don’t re-scrape tag/diary on every refresh; only **film-page checks** run for missing or updated data.

## Where it’s stored

- **Directory:** `CINEPHILES_DATA_DIR` (default: `./data` in the project).
- **Files:** one per user: `data/stats_<username>.json`.
- On Render, set `CINEPHILES_DATA_DIR` to a path on a **persistent disk** if you add one; otherwise the default is used (ephemeral on free tier).

## Shape of persisted data

Each `stats_<username>.json` looks like:

```json
{
  "username": {
    "films": {
      "film-slug": {
        "slug": "film-slug",
        "title": "Film Title (year)",
        "rating": 4,
        "has_review": true,
        "word_count": 120,
        "review_link": "https://letterboxd.com/username/film/film-slug/",
        "url": "https://..."
      }
    },
    "stats": { "rotw_count": 5 }
  }
}
```

- **films:** only films the user has **watched** (we never store “not watched”; we just omit the slug).
- **stats:** optional; used for ROTW and similar.

## Refresh strategy (film-page only)

1. **Load** from persistence (`load_all_users_films()`).
2. For each user:
   - If we already have **films** for that user → use them (no requests).
   - If not → for each **selected slug** we call  
     `GET https://letterboxd.com/<username>/film/<slug>/`  
     - **404** → not watched → do not add to cache.  
     - **200** → parse page for rating + review (word count, link) → **update persistence**.
3. No tag or diary scraping; **one request per film** we need to check.

So after the first run (or after a full scrape from “Refresh user”), later loads only hit the film URL for any missing slugs.

## When a full scrape still runs

- **Refresh user** (e.g. `/refresh/<username>`) still calls `get_all_user_logs` (tag or diary scrape) and then **saves the result to persistence**, so future index loads can use film-page-only.
- **First time** a user has no data in persistence, the index uses **film-page-only** for that user (no full scrape) and fills the cache from those film pages.

## Bootstrap (optional)

To prime persistence from a full scrape once:

1. Run a full refresh for each user (e.g. hit “Refresh” in the UI for each), or  
2. Load the index once with the **old behavior** (temporarily use `get_all_user_logs` instead of `get_all_user_logs_from_film_pages` when cache is empty) so one full scrape runs and is saved.

The current index uses **film-page-only** when cache is empty, so the first load for a new user only does N film-page requests (N = number of selected slugs).
