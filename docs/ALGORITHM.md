# Algorithm: Cache + Persistence, Minimal Letterboxd Scraping

## Data sources

| Source | What it holds | When it’s used |
|--------|----------------|----------------|
| **Google Sheet – Selected** | List of club movies: SLUG, TITLE, WATCHED_DATE, ROTW, … | Defines *which* films we care about (selected_slugs). |
| **Google Sheet – Users** | Letterboxd usernames | Who to show film data for. |
| **Persistence** (e.g. `./data/stats_{username}.json` or FilmLog sheet) | Per user: which of the *selected* films they’ve watched + rating/review. One row (or entry) per (user, slug) **only when watched**. | First place we look for “user X watched film Y” and rating/review. |
| **Cache** (`/tmp/stats_{username}_cache.json`) | Same shape as persistence: films + stats (e.g. rotw_count). Ephemeral. | Fallback when persistence is empty; also written by full scrape and ROTW. |

We **never** store “not watched” in persistence or cache; we only store entries for films they *have* watched.

---

## When we hit Letterboxd

We only need to know, for each (user, selected_slug): **did they watch it, and if so rating/review?**

- **One URL per (user, slug):**  
  `GET https://letterboxd.com/<username>/film/<slug>/`  
  - **404** → not watched → do not add to persistence/cache.  
  - **200** → parse page → add/update that (user, slug) in persistence and cache.

We **do not** use tag or diary scraping for normal refresh. Full tag/diary scrape is only used when you explicitly “Refresh user” (and then we write results to both cache and persistence).

---

## Flow 1: Index (home page) – minimize requests

**Goal:** Show stats for all users and selected films without scraping more than necessary.

1. **Selected list**  
   Read from Google Sheet (or cache): `selected_slugs`, `selected_records`.

2. **Film data: single source of truth**  
   - Prefer **persistence** (e.g. `load_all_users_films()` from data dir or FilmLog sheet).  
   - If empty, fall back to **cache** (`load_all_stats_caches_in_memory()` from /tmp).

3. **Per user**  
   - If we already have **films** for that user (from persistence or cache):  
     - Use it. **No Letterboxd requests.**  
   - If we’re missing films for that user:  
     - For each `slug` in `selected_slugs` that is **not** in that user’s films:  
       - One request: `GET letterboxd.com/<username>/film/<slug>/`.  
       - 404 → skip (don’t add).  
       - 200 → parse, then **update persistence and cache** for that (user, slug).  
     - So we only request **missing (user, slug)** pairs.

4. **ROTW**  
   - From cache/persistence when present; otherwise compute from `selected_records` (ROTW column) and then **write ROTW counts into cache** (and optionally persistence) so next time we don’t recompute.

**Result:** After the first load (or after a “meeting complete” warm – see below), most index loads use only persistence/cache and **do zero Letterboxd requests**.

---

## Flow 2: Refresh user (manual)

- Run a **full** scrape for that user (tag or diary) and get all selected films.  
- **Write results to both cache and persistence** for that user.  
- After that, index uses that data and doesn’t need to hit Letterboxd for that user until new films are added to Selected.

---

## Flow 3: Meeting complete (mark movie complete)

When you mark a movie as “complete” after a meeting:

1. **Sheets**  
   - Add a new row to **Selected** (new SLUG, WATCHED_DATE, ROTW, …).  
   - Update Watchlist (IS_WATCHED, clear IS_SELECTED, etc.).  
   - Update in-memory **cache** for `selected_records` (and watchlist/nominated) so the app sees the new selected list immediately.

2. **Update cache and persistence for the new film**  
   - For the **new slug only**, for **each user**:  
     - One request: `GET letterboxd.com/<username>/film/<new_slug>/`.  
     - 404 → don’t add.  
     - 200 → parse and **update persistence and cache** for that (user, slug).  
   - So we do **N requests** (one per user) for the one new slug, not for all films.

3. **ROTW**  
   - Selected sheet already has the new ROTW in the new row.  
   - Next time we need ROTW we read from Selected (or cache); optionally refresh ROTW in cache/persistence so index stays fast.

**Result:** After “meeting complete”, cache and persistence already contain the new film for every user (where they’ve watched it). The **next index load** can use that data and do **zero** Letterboxd requests.

---

## Summary

- **Single source of truth for “user X watched film Y”:** persistence (and cache as copy).  
- **Index:** Use persistence first, then cache. Only request Letterboxd for **(user, slug)** pairs that are in `selected_slugs` but **missing** from persistence/cache.  
- **Meeting complete:** Update Selected sheet and app cache; then **warm** persistence and cache for the **new slug only** (one request per user).  
- **Refresh user:** Full scrape once, then write to both cache and persistence; after that, no Letterboxd until new films are added.

This keeps Letterboxd requests to a minimum: only when new films are added (on index or at meeting complete) and only one request per (user, slug).
