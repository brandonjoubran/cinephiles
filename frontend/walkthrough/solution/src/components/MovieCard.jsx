/**
 * STEP 4 — A reusable card component
 *
 * Props:
 *   movie    — one item from GET /movies
 *   onNominate — parent handles API + refresh
 */
export default function MovieCard({ movie, onNominate }) {
  const isNominated = movie.status === "nominated";
  const isSelected = movie.status === "selected";

  return (
    <article className={`movie-card ${isNominated ? "movie-card--nominated" : ""} ${isSelected ? "movie-card--selected" : ""}`}>
      {movie.poster ? (
        <img className="movie-card__poster" src={movie.poster} alt="" />
      ) : (
        <div className="movie-card__poster movie-card__poster--empty">No poster</div>
      )}

      <div className="movie-card__body">
        <h2 className="movie-card__title">
          <a href={movie.url} target="_blank" rel="noreferrer">
            {movie.title}
          </a>
        </h2>
        <p className="movie-card__meta">
          Added by <strong>{movie.added_by}</strong> · {movie.date_added}
        </p>
        <p className="movie-card__status">
          Status: <code>{movie.status}</code>
          {movie.nominated_by ? ` · nominated by ${movie.nominated_by}` : ""}
        </p>

        {movie.status === "backlog" && (
          <button type="button" className="movie-card__btn" onClick={() => onNominate(movie.slug)}>
            Nominate
          </button>
        )}
      </div>
    </article>
  );
}
