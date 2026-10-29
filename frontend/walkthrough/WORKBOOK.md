# Hands-on workbook — build React yourself

You are **not** reading reference files and hoping they make sense. You are **typing** into `lab/` and checking the browser after every step.

| Folder | What it is |
|--------|------------|
| **`lab/`** | **Your project.** Only edit files here. |
| **`solution/`** | Finished answer. Open only if stuck after trying. |
| **`steps/`** | Old snippets — ignore; use this workbook instead. |

Keep two terminals open the whole time:

1. **API** — `uvicorn main:app --reload`
2. **Lab** — `cd lab && npm run dev` → http://localhost:5174

---

## How you know a step worked

After every step you must see a **visible change** in the browser (or in DevTools → Network). If nothing changes, stop and fix before continuing.

---

## Step 1 — Prove hot reload works (~5 min)

**Files you touch:** `lab/src/App.jsx` only.

### Do this

1. With `npm run dev` running, open http://localhost:5174.
2. In Cursor, open `frontend/walkthrough/lab/src/App.jsx`.
3. Find the `<h1>React lab</h1>` line.
4. Change it to: `<h1>Hello, I am learning React</h1>`
5. Save the file (Cmd+S).

### Check

- The browser title area should show **Hello, I am learning React** within 1–2 seconds.
- You did **not** refresh the page manually (Vite did it for you).

### If it failed

- Terminal 2 must say something like `Local: http://localhost:5174/`.
- Wrong folder? You must run `npm run dev` from `lab/`, not from `frontend/`.

### You learned

- `App.jsx` is what appears on screen.
- Saving a file updates the browser.

---

## Step 2 — Create the API helper file (~15 min)

**Files you create:** `lab/src/api/client.js` (new file).

### Do this

1. In Cursor, right-click the `lab/src` folder → **New Folder** → name it `api`.
2. Right-click `api` → **New File** → name it `client.js`.
3. Type this entire file (line by line is fine):

```js
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || response.statusText);
  }

  return response.json();
}

export function getMovies() {
  return api("/movies");
}
```

4. Save.

5. Make sure `lab/.env` exists (copy from `.env.example` if needed):

```
VITE_API_URL=http://127.0.0.1:8000
```

6. If you just created `.env`, stop the dev server (Ctrl+C) and run `npm run dev` again.

### Do this (wire a test button in App)

7. Replace **all** of `lab/src/App.jsx` with:

```jsx
import { getMovies } from "./api/client.js";

export default function App() {
  async function testApi() {
    try {
      const data = await getMovies();
      alert("Got " + data.length + " movies from the API");
      console.log(data);
    } catch (err) {
      alert("Error: " + err.message);
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <h1>Step 2 — API test</h1>
      <button type="button" onClick={testApi}>
        Click me to fetch /movies
      </button>
    </div>
  );
}
```


9. Save.

### Check

1. Browser shows a button **Click me to fetch /movies**.
2. Click it.
3. You get an alert like **Got 3 movies** (number may differ) OR **Got 0 movies**.
4. Open DevTools (F12) → **Console** — you should see an array of objects printed.

### If it failed

| Symptom | Fix |
|---------|-----|
| `Failed to fetch` | API terminal not running, or wrong URL in `.env` |
| CORS error in console | Restart API (CORS allows port 5174) |
| `Cannot find module './api/client.js'` | Folder must be `src/api/client.js` exactly |
| Alert says Error 404 | Check API: http://127.0.0.1:8000/movies in browser |

### You learned

- `client.js` talks to Python; `App.jsx` calls `getMovies()`.
- `async` / `await` waits for the network.
- `console.log` is your friend.

---

## Step 3 — Show raw JSON on the page (~10 min)

**Files you touch:** `lab/src/App.jsx`.

### Do this

1. Replace all of `App.jsx` with:

```jsx
import { useEffect, useState } from "react";
import { getMovies } from "./api/client.js";

export default function App() {
  const [movies, setMovies] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getMovies()
      .then((data) => setMovies(data))
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return <p style={{ padding: 24, color: "red" }}>Error: {error}</p>;
  }

  if (movies.length === 0) {
    return <p style={{ padding: 24 }}>Loading… (or no movies on sheet)</p>;
  }

  return (
    <pre style={{ padding: 24, fontSize: 12 }}>
      {JSON.stringify(movies, null, 2)}
    </pre>
  );
}
```

2. Save.

### Check

- First you may briefly see **Loading…**
- Then you see **JSON text** on the page (titles, slugs, status, etc.)

### If it failed

- Read the red error message on screen.
- Compare your file to `solution/src/App.jsx` only after you tried.

### You learned

- **`useState([])`** — holds data that can change.
- **`useEffect(..., [])`** — run once when page loads.
- **`setMovies(data)`** — put API result in state → React redraws.

---

## Step 4 — Create one MovieCard (~20 min)

**Files you create:** `lab/src/components/MovieCard.jsx`.

### Do this

1. New folder: `lab/src/components`.
2. New file: `lab/src/components/MovieCard.jsx`.
3. Type:

```jsx
export default function MovieCard({ movie }) {
  return (
    <article
      style={{
        display: "flex",
        gap: 12,
        background: "#fff",
        padding: 12,
        borderRadius: 8,
        boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
      }}
    >
      {movie.poster ? (
        <img src={movie.poster} alt="" style={{ width: 72, borderRadius: 4 }} />
      ) : (
        <div style={{ width: 72, background: "#eee" }} />
      )}
      <div>
        <h2 style={{ margin: "0 0 4px", fontSize: 18 }}>{movie.title}</h2>
        <p style={{ margin: 0, color: "#666", fontSize: 14 }}>
          Added by {movie.added_by} · status: <strong>{movie.status}</strong>
        </p>
      </div>
    </article>
  );
}
```

5. Save.

### Do this (use the card once)

6. At the top of `App.jsx` add:

```jsx
import MovieCard from "./components/MovieCard.jsx";
```

7. Replace the `<pre>...</pre>` return block with:

```jsx
  return (
    <div style={{ padding: 24 }}>
      <h1>Step 4 — one card</h1>
      <MovieCard movie={movies[0]} />
    </div>
  );
```

8. Save.

### Check

- You see **one** card with poster (if any), title, added_by, status.
- Not JSON dump anymore.

### If it failed

- White screen → red error in DevTools Console (often a typo in JSX).
- `movies[0]` undefined → need at least one movie on sheet; add via main app or API.

### You learned

- **Component** = function that returns UI.
- **`movie={movies[0]}`** passes one object as a prop.
- Inside the card, use `movie.title`, `movie.status`, etc.

---

## Step 5 — Show every movie as a card (~10 min)

**Files you touch:** `lab/src/App.jsx`.

### Do this

1. Change the return section to:

```jsx
  return (
    <div style={{ padding: 24 }}>
      <h1>Step 5 — all movies ({movies.length})</h1>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {movies.map((movie) => (
          <MovieCard key={movie.slug} movie={movie} />
        ))}
      </div>
    </div>
  );
```

2. Save.

### Check

- You see **multiple** cards stacked vertically.
- Count in the title matches number of cards.

### You learned

- **`.map()`** turns an array into a list of UI.
- **`key={movie.slug}`** — React needs a stable id per row.

---

## Step 6 — Nominate button (~20 min)

**Files you touch:** `client.js`, `MovieCard.jsx`, `App.jsx`.

### Do this — client.js

1. Open `lab/src/api/client.js`.
2. Add at the bottom:

```js
export function nominateMovie(slug, username) {
  return api(`/movies/${slug}/nominate`, {
    method: "POST",
    body: { username },
  });
}
```

3. Save.

### Do this — MovieCard.jsx

4. Change the first line to accept a second prop:

```jsx
export default function MovieCard({ movie, onNominate }) {
```

5. Before the closing `</article>`, add (inside the card, after the text):

```jsx
        {movie.status === "backlog" && (
          <button
            type="button"
            style={{ marginTop: 8, padding: "6px 12px" }}
            onClick={() => onNominate(movie.slug)}
          >
            Nominate
          </button>
        )}
```

6. Save.

### Do this — App.jsx

7. Change import line to:

```jsx
import { getMovies, nominateMovie } from "./api/client.js";
```

8. Add this function **inside** `App`, after `useEffect`:

```jsx
  const username = "bjoubs"; // change to your Letterboxd username

  async function handleNominate(slug) {
    await nominateMovie(slug, username);
    const data = await getMovies();
    setMovies(data);
  }
```

9. Change each card line to:

```jsx
          <MovieCard key={movie.slug} movie={movie} onNominate={handleNominate} />
```

10. Save.

### Check

1. Find a card with **status: backlog**.
2. Click **Nominate**.
3. Card should update (orange border if you add styles later; at minimum **status** becomes `nominated` after reload).
4. DevTools → **Network**: see `POST .../nominate` then `GET .../movies`.

### If it failed

- Button not visible → film is not `backlog` (already nominated).
- 400 error → read alert / network response body.

### You learned

- Child calls `onNominate(slug)`; parent runs API.
- After changing data on server, **fetch again** to refresh the list.

---

## Step 7 — Add simple CSS file (~10 min)

**Files you create:** `lab/src/App.css`, edit `main.jsx`.

### Do this

1. Create `lab/src/App.css` with:

```css
.page {
  max-width: 640px;
  margin: 0 auto;
  padding: 24px;
}

.movie-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.movie-card--nominated {
  border-left: 4px solid orange;
}
```

2. In `main.jsx`, add under the App import:

```jsx
import "./App.css";
```

3. In `MovieCard.jsx`, change `<article` to:

```jsx
    <article
      className={
        movie.status === "nominated" ? "movie-card movie-card--nominated" : "movie-card"
      }
```

4. In `App.jsx`, use `className="page"` on the outer div and `className="movie-list"` on the list div.

5. Save all files.

### Check

- Nominated films have an **orange left border**.

### You learned

- CSS files are imported from `main.jsx`.
- `className` = React’s `class`.

---

## You are done with the lab

Compare your `lab/` folder to `solution/`:

```bash
diff -ru lab/src solution/src
```

Small differences are fine. Behavior should match: list films, nominate backlog film.

---

## What to do next in the real app

| Lab file | Real app file |
|----------|----------------|
| `lab/src/api/client.js` | `frontend/src/api/client.js` |
| `lab/src/components/MovieCard.jsx` | `frontend/src/components/MovieCard.jsx` |
| `lab/src/App.jsx` | `frontend/src/pages/WatchlistPage.jsx` |

Open `frontend/src/App.jsx` and see **Layout** + **routes** — same ideas, more files.

---

## Cheat sheet

```jsx
// state
const [x, setX] = useState(initial);

// load on mount
useEffect(() => { load(); }, []);

// list
items.map((item) => <Card key={item.id} item={item} />)

// fetch
const data = await getMovies();
```

---

## When stuck

1. Read the error in the browser (red text) or DevTools → Console.
2. Check Network tab for failed requests.
3. Only then open `solution/src/...` for that step.
4. Ask: “Step N — I see [error] after [action]” with a screenshot if possible.
