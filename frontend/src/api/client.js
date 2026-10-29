const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function api(path, options = {}) {
  const headers = { ...options.headers };
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    body:
      options.body && !(options.body instanceof FormData)
        ? JSON.stringify(options.body)
        : options.body,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail || (typeof data.error === "string" ? data.error : detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

export const getStatsPage = () => api("/view/stats");
export const refreshUser = (username) => api(`/view/stats/refresh/${username}`, { method: "POST" });
export const getWatchlistPage = () => api("/view/watchlist");
export const getMeetingsPage = () => api("/view/meetings");
export const getLeaderboardPage = () => api("/view/leaderboard");
export const generateNominators = () => api("/nominators/generate");

export const addMovie = (url, added_by) =>
  api("/movies", { method: "POST", body: { url, added_by } });
export const deleteMovie = (slug) => api(`/movies/${slug}`, { method: "DELETE" });
export const nominateMovie = (slug, username) =>
  api(`/movies/${slug}/nominate`, { method: "POST", body: { username } });
export const voteMovie = (slug, username) =>
  api(`/movies/${slug}/vote`, { method: "POST", body: { username } });
export const selectMovie = (slug) => api(`/movies/${slug}/select`, { method: "POST" });
export const completeMovie = (slug, rotw = []) =>
  api(`/movies/${slug}/complete`, { method: "POST", body: { rotw } });
export const markWatched = (slug) => api(`/movies/${slug}/mark-watched`, { method: "POST" });
export const markUnwatched = (slug) => api(`/movies/${slug}/mark-unwatched`, { method: "POST" });
export const addMeeting = (body) => api("/view/meetings", { method: "POST", body });
