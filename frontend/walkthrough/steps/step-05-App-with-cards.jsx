/**
 * STEP 5 — Render a list of cards
 * Each movie in the array becomes one <MovieCard /> (key={movie.slug} is required).
 */
import { useEffect, useState } from "react";
import { getMovies } from "./api/client.js";
import MovieCard from "./components/MovieCard.jsx";

export default function App() {
  const [movies, setMovies] = useState([]);

  useEffect(() => {
    getMovies().then(setMovies);
  }, []);

  return (
    <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
      <h1>Movies ({movies.length})</h1>
      {movies.map((movie) => (
        <MovieCard key={movie.slug} movie={movie} />
      ))}
    </div>
  );
}
