"""
FilmLog Google Sheet as durable source of truth for watched films.

- Read: load_all_from_film_log_sheet() -> same shape as load_all_users_films().
  Use when persistence (JSON) and /tmp cache are empty so the sheet hydrates the app.
- Write: sync_user_films_to_sheet(username, films_dict) after every persistence write.
  Keeps the sheet in sync with JSON + cache.

Schema: USERNAME, SLUG, TITLE, RATING, HAS_REVIEW, WORD_COUNT, REVIEW_LINK, UPDATED_AT.
See docs/FILM_LOG_SHEET_SCHEMA.md.
"""

from datetime import datetime

# Headers must match FilmLog sheet row 1
HEADERS = ["USERNAME", "SLUG", "TITLE", "RATING", "HAS_REVIEW", "WORD_COUNT", "REVIEW_LINK", "UPDATED_AT"]


def _get_sheet():
    try:
        from db import get_film_log_sheet
        return get_film_log_sheet()
    except Exception as e:
        print(f"[FilmLog] Sheet not available: {e}")
        return None


def load_all_from_film_log_sheet():
    """
    Read FilmLog sheet and return same shape as load_all_users_films():
    { username: { "films": { slug: { title, rating, has_review, word_count, review_link } }, "stats": {} } }.
    Returns {} if sheet is missing or empty.
    """
    sheet = _get_sheet()
    if not sheet:
        return {}
    try:
        rows = sheet.get_all_records()
    except Exception as e:
        print(f"[FilmLog] Failed to read sheet: {e}")
        return {}
    combined = {}
    for row in rows:
        username = (row.get("USERNAME") or "").strip()
        slug = (row.get("SLUG") or "").strip()
        if not username or not slug:
            continue
        if username not in combined:
            combined[username] = {"films": {}, "stats": {}}
        rating = row.get("RATING")
        if rating != "" and rating is not None:
            try:
                rating = float(rating)
            except (TypeError, ValueError):
                rating = None
        has_review = row.get("HAS_REVIEW")
        if isinstance(has_review, str):
            has_review = has_review.upper() in ("TRUE", "1", "YES")
        elif not isinstance(has_review, bool):
            has_review = bool(has_review)
        word_count = row.get("WORD_COUNT")
        if word_count != "" and word_count is not None:
            try:
                word_count = int(word_count)
            except (TypeError, ValueError):
                word_count = 0
        else:
            word_count = 0
        combined[username]["films"][slug] = {
            "slug": slug,
            "title": row.get("TITLE") or "",
            "rating": rating,
            "has_review": has_review,
            "word_count": word_count,
            "review_link": row.get("REVIEW_LINK") or "",
            "url": row.get("REVIEW_LINK") or "",
        }
    return combined


def _film_to_row(username, slug, entry):
    """Build a sheet row (list) from a film entry dict."""
    rating = entry.get("rating")
    if rating is None:
        rating = ""
    has_review = entry.get("has_review", False)
    word_count = entry.get("word_count") or 0
    review_link = entry.get("review_link") or entry.get("url") or ""
    title = entry.get("title") or ""
    updated_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    return [
        username,
        slug,
        title,
        rating,
        "TRUE" if has_review else "FALSE",
        word_count,
        review_link,
        updated_at,
    ]


def sync_user_films_to_sheet(username, films_dict):
    """
    Upsert one row per (username, slug) in films_dict into the FilmLog sheet.
    If a row with same USERNAME+SLUG exists, update it; otherwise append.
    """
    if not films_dict:
        return
    sheet = _get_sheet()
    if not sheet:
        return
    try:
        all_values = sheet.get_all_values()
    except Exception as e:
        print(f"[FilmLog] Failed to read sheet for sync: {e}")
        return
    if not all_values:
        # Empty sheet: add headers and append all rows
        sheet.append_row(HEADERS)
        for slug, entry in films_dict.items():
            sheet.append_row(_film_to_row(username, slug, entry))
        print(f"[FilmLog] Appended {len(films_dict)} rows for {username}")
        return
    headers = all_values[0]
    # Normalize header indices (sheet may have different order)
    col_idx = {}
    for i, h in enumerate(headers):
        col_idx[h.strip().upper()] = i
    username_col = col_idx.get("USERNAME", 0)
    slug_col = col_idx.get("SLUG", 1)
    # Build set of (username, slug) we want to write
    to_write = {(username, slug): _film_to_row(username, slug, entry) for slug, entry in films_dict.items()}
    # Map (username, slug) -> 1-based row index for existing rows
    existing = {}
    for i in range(1, len(all_values)):
        row = all_values[i]
        if len(row) > max(username_col, slug_col):
            u, s = (row[username_col] or "").strip(), (row[slug_col] or "").strip()
            if u and s:
                existing[(u, s)] = i + 1  # 1-based
    updated = 0
    appended = 0
    for (u, slug), row_values in to_write.items():
        key = (u, slug)
        if key in existing:
            row_num = existing[key]
            range_str = f"A{row_num}:H{row_num}"
            sheet.update(range_str, [row_values])
            updated += 1
        else:
            sheet.append_row(row_values)
            appended += 1
    if updated or appended:
        print(f"[FilmLog] Synced {username}: {updated} updated, {appended} appended")
