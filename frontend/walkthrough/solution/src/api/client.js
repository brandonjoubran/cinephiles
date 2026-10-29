/**
 * STEP 2 — API client
 * All backend URLs live here so pages stay readable.
 */
const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || response.statusText);
  }

  return response.json();
}

/** GET /movies — list every film on the club watchlist */
export function getMovies() {
  return api("/movies");
}

/** POST /movies/{slug}/nominate — toggle nomination for a user */
export function nominateMovie(slug, username) {
  return api(`/movies/${slug}/nominate`, {
    method: "POST",
    body: { username },
  });
}
