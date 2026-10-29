/**
 * STEP 3 — Fetch on mount (no cards yet)
 * Replace App.jsx with this, then open the browser console to see the data.
 */
import { useEffect, useState } from "react";
import { getMovies } from "./api/client.js";

export default function App() {
  const [movies, setMovies] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getMovies()
      .then(setMovies)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <p>Error: {error}</p>;
  if (!movies.length) return <p>Loading or empty…</p>;

  return (
    <pre style={{ padding: 16 }}>
      {JSON.stringify(movies, null, 2)}
    </pre>
  );
}
