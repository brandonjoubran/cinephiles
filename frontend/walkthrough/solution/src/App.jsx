/**
 * STEP 3 + 5 + 6 — Page component: fetch data, show cards, handle actions
 */
import { useCallback, useEffect, useState } from "react";
import { getMovies, nominateMovie } from "./api/client.js";
import MovieCard from "./components/MovieCard.jsx";

export default function App() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [username, setUsername] = useState("bjoubs");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await getMovies();
      setMovies(list);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleNominate = async (slug) => {
    if (!username.trim()) {
      alert("Pick a username first");
      return;
    }
    try {
      await nominateMovie(slug, username.trim());
      await load();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="app">
      <header className="app__header">
        <h1>Walkthrough: mini watchlist</h1>
        <p className="app__hint">
          This sandbox calls your real API at{" "}
          <code>{import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"}</code>
        </p>
        <label className="app__user">
          Acting as:{" "}
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </label>
        <button type="button" onClick={load}>
          Reload
        </button>
      </header>

      {loading && <p className="app__message">Loading movies…</p>}
      {error && <p className="app__error">Error: {error}</p>}

      <section className="movie-list">
        {movies.map((movie) => (
          <MovieCard key={movie.slug} movie={movie} onNominate={handleNominate} />
        ))}
      </section>

      {!loading && !error && movies.length === 0 && (
        <p className="app__message">No movies yet. Add one via the main app or API.</p>
      )}
    </div>
  );
}
