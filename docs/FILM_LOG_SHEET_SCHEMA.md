# Film Log sheet schema (Google Sheet as DB)

Use this as the **single source of truth** for “user X watched film Y” and their rating/review. One row per **(username, slug)** — only films they have **watched** are stored.

---

## Sheet name

**`FilmLog`** (add a new tab with this name in your OnlyCinephilesDB spreadsheet)

---

## Columns (row 1 = headers)

| Column       | Type    | Required | Description |
|-------------|---------|----------|-------------|
| **USERNAME** | text    | yes      | Letterboxd username (e.g. `bjoubs`) |
| **SLUG**     | text    | yes      | Film slug (e.g. `heat-1995`). Matches Selected sheet SLUG. |
| **TITLE**    | text    | no       | Display title (e.g. `Heat (1995)`). |
| **RATING**   | number  | no       | 0–5, half stars (0.5, 1, 1.5, …, 5). Blank if they didn’t rate. |
| **HAS_REVIEW** | boolean | no     | TRUE/FALSE or 1/0. |
| **WORD_COUNT** | number | no      | Review word count; 0 if no review. |
| **REVIEW_LINK** | text   | no       | Full URL: `https://letterboxd.com/<username>/film/<slug>/` |
| **UPDATED_AT**  | text   | no       | When we last checked Letterboxd (e.g. `2025-02-15T14:30:00`). |

---

## Row 1 (header row)

```
USERNAME	SLUG	TITLE	RATING	HAS_REVIEW	WORD_COUNT	REVIEW_LINK	UPDATED_AT
```

(Use tabs between columns if you paste; in the sheet each column is its own cell.)

---

## Rules

- **One row per (USERNAME, SLUG).** No duplicate (USERNAME, SLUG).
- **Only watched films.** If they didn’t watch it, there is no row (we don’t store “not watched”).
- **Lookup:** “Did user X watch film Y?” → look for a row with USERNAME = X and SLUG = Y. Found = watched; not found = not watched (or not yet checked).
- **Refresh:** When we check Letterboxd (`letterboxd.com/<username>/film/<slug>/`), 200 → upsert this row; 404 → delete row if present (or leave absent).

---

## Optional: User stats sheet

If you want to persist ROTW (or other per-user stats) in the same workbook, add a second tab:

**Sheet name:** `UserStats`

| Column       | Type   | Description |
|-------------|--------|-------------|
| **USERNAME** | text   | Letterboxd username |
| **ROTW_COUNT** | number | Review of the week count |
| **UPDATED_AT** | text  | Last updated |

Row 1: `USERNAME	ROTW_COUNT	UPDATED_AT`

You can add this later; the app can keep computing ROTW from Selected/other sheets until then.
