import { useState } from "react";

export default function MovieCard({
  movie,
  onDelete,
  onNominate,
  onVote,
  onSelect,
  onComplete,
  onMarkWatched,
  onMarkUnwatched,
  onRemoveNomination,
}) {
  const [open, setOpen] = useState(movie.IS_SELECTED || movie.IS_NOMINATED);

  const cardClass = [
    "card",
    movie.IS_WATCHED ? "card-watched" : "",
    movie.IS_NOMINATED ? "card-nominated" : "",
    movie.IS_SELECTED ? "card-selected" : "",
    open ? "open" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={cardClass}>
      <button type="button" className="delete-btn" data-slug={movie.SLUG} onClick={() => onDelete(movie.SLUG)}>
        ×
      </button>
      <button type="button" className="card-toggle" onClick={() => setOpen((v) => !v)}>
        <img className="toggle-poster" src={movie.POSTER} alt={movie.TITLE} />
        <div className="toggle-content">
          <span className="card-title">{movie.TITLE}</span>
          <span className="toggle-icon">⌄</span>
        </div>
      </button>

      <div className="card-details">
        <div className="card-inner">
          {movie.IS_NOMINATED || movie.IS_SELECTED ? (
            <img className="card-img" src={movie.POSTER} alt={`${movie.TITLE} Poster`} />
          ) : (
            <img className="card-img not-nom" src={movie.POSTER} alt={`${movie.TITLE} Poster`} />
          )}
          <div className="card-content">
            <a className="card-title" href={movie.URL} target="_blank" rel="noopener noreferrer">
              {movie.TITLE}
            </a>
            <div className="card-meta">
              <strong>{movie.ADDED_BY}</strong> - {movie.DATE_ADDED}
            </div>

            {movie.IS_NOMINATED ? (
              <div className="card-nomination">
                🎯 <span className="status-highlight">Nominated</span>
                <br />
                <span className="nominator">
                  Nominated by <strong>{movie.NOMINATED_BY}</strong>
                </span>
                <br />
                {movie.VOTED_BY?.length ? (
                  <div className="meta">
                    Votes: <strong>{movie.VOTED_BY.join(", ")}</strong>
                  </div>
                ) : null}
              </div>
            ) : null}

            {movie.IS_SELECTED ? (
              <div className="card-select">
                ✅ <span className="status-highlight-selected">Won vote</span>
                <br />
                {movie.VOTED_BY?.length ? (
                  <div className="meta">
                    Votes: <strong>{movie.VOTED_BY.join(", ")}</strong>
                  </div>
                ) : null}
              </div>
            ) : null}

            {movie.IS_WATCHED ? (
              <div className="card-watched-label">
                <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
                  <span style={{ fontSize: "1.1em" }}>
                    ✅ <strong>Watched</strong>
                  </span>
                  {movie.WATCHED_DATE ? (
                    <span
                      style={{
                        color: "#00796b",
                        borderLeft: "2px solid #b2dfdb",
                        paddingLeft: "10px",
                        marginLeft: "8px",
                      }}
                    >
                      <span style={{ fontSize: "0.98em" }}>
                        📅 Date: <strong>{movie.WATCHED_DATE}</strong>
                      </span>
                    </span>
                  ) : null}
                  {movie.AVG_RATING ? (
                    <span
                      style={{
                        color: "#ff9800",
                        borderLeft: "2px solid #ffe0b2",
                        paddingLeft: "10px",
                        marginLeft: "8px",
                      }}
                    >
                      <span style={{ fontSize: "0.98em" }}>
                        ⭐ Avg rating: <strong>{movie.AVG_RATING}</strong>
                      </span>
                    </span>
                  ) : null}
                </div>
              </div>
            ) : null}
          </div>

          <div className="card-actions">
            {!movie.IS_WATCHED && !movie.IS_NOMINATED && movie.IS_SELECTED ? (
              <button type="button" className="action-btn watched-btn" onClick={() => onComplete(movie.SLUG)}>
                ✅ Complete
              </button>
            ) : null}
            {!movie.IS_WATCHED && !movie.IS_NOMINATED && !movie.IS_SELECTED ? (
              <button type="button" className="action-btn nominate-btn" onClick={() => onNominate(movie.SLUG)}>
                🏆 Nominate
              </button>
            ) : null}
            {movie.IS_NOMINATED ? (
              <>
                <button type="button" className="action-btn vote-btn" onClick={() => onVote(movie.SLUG)}>
                  🗳️ Vote
                </button>
                <button type="button" className="action-btn remove-nominate-btn" onClick={() => onRemoveNomination(movie.SLUG)}>
                  ❌ Remove Nomination
                </button>
                <button type="button" className="action-btn winning-btn" onClick={() => onSelect(movie.SLUG)}>
                  ✅ Winning Nomination
                </button>
              </>
            ) : null}
            {!movie.IS_WATCHED && !movie.IS_SELECTED ? (
              <button type="button" className="action-btn watched-btn" onClick={() => onMarkWatched(movie.SLUG)}>
                🎬 Watched
              </button>
            ) : null}
            {movie.IS_WATCHED ? (
              <button type="button" className="action-btn watched-btn" onClick={() => onMarkUnwatched(movie.SLUG)}>
                Mark as Unwatched
              </button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
