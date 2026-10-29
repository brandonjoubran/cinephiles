/**
 * STEP 4 — One card component
 * Copy to: src/components/MovieCard.jsx
 * (Same as sandbox — see comments inside file)
 */
export default function MovieCard({ movie }) {
  return (
    <article style={{ display: "flex", gap: 12, background: "#fff", padding: 12, borderRadius: 8 }}>
      <img src={movie.poster} alt="" style={{ width: 80 }} />
      <div>
        <h2 style={{ margin: 0 }}>{movie.title}</h2>
        <p style={{ margin: "4px 0", color: "#666" }}>{movie.status}</p>
      </div>
    </article>
  );
}
