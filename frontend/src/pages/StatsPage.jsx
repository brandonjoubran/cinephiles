import { useCallback, useEffect, useState } from "react";
import ClubNav from "../components/ClubNav.jsx";
import { getStatsPage, refreshUser } from "../api/client.js";
import "../styles/stats.css";

export default function StatsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setData(await getStatsPage());
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = async (username) => {
    await refreshUser(username);
    await load();
  };

  if (error) {
    return (
      <div className="stats-root">
        <ClubNav />
        <p className="page-error">Error: {error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="stats-root">
        <ClubNav />
        <p className="page-loading">Loading…</p>
      </div>
    );
  }

  const {
    summary,
    most_divisive,
    most_divisive_stddev,
    most_liked,
    least_liked,
    longest_review,
    shortest_review,
  } = data;

  return (
    <div className="stats-root">
      <ClubNav />
      <div className="stats-logo">
        <img src="/logo.png" alt="Letterboxd Stats Logo" />
      </div>
      <div className="container">
        <h2>Summary</h2>
        <div className="summary-grid">
          {summary.map((user) => (
            <div className="summary-card" key={user.username}>
              <div className="summary-card__body">
                <a
                  href={`https://letterboxd.com/${user.username}/tag/onlycinephiles/films/`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <div>
                    <strong>{user.username}</strong>
                    {user.watched} watched ({user.percentage}%)
                    {user.streak ? (
                      <span className="streak" title="Current streak (consecutive from latest)">
                        {" "}
                        {user.streak}🔥
                      </span>
                    ) : null}
                    <br />
                    Avg rating: <span className="highlight">{user.avg_rating}</span>
                    <br />
                    {user.reviews} reviews
                    <br />
                    Avg words: <span className="highlight">{user.avg_words}</span>
                    <br />
                    ROTW:{" "}
                    <span className="highlight">{user.rotw_count || 0} 🏆</span>
                    <br />
                  </div>
                </a>
                <button type="button" className="refresh-btn" onClick={() => onRefresh(user.username)}>
                  🔄 Refresh
                </button>
              </div>
            </div>
          ))}
        </div>

        <h2>Most Divisive Movie</h2>
        <p>
          {most_divisive_stddev > 0 ? (
            <>
              <span className="highlight">{most_divisive?.[0]}</span> (std dev: {most_divisive_stddev})
            </>
          ) : (
            "No divisive movie data available."
          )}
        </p>

        <h2>Most Liked Movie</h2>
        <p>
          <span className="highlight">{most_liked?.[0]}</span> ({Number(most_liked?.[1] || 0).toFixed(2)}⭐)
        </p>

        <h2>Least Liked Movie</h2>
        <p>
          <span className="highlight">{least_liked?.[0]}</span> ({Number(least_liked?.[1] || 0).toFixed(2)}⭐)
        </p>

        <h2>Longest Review</h2>
        <p>
          {longest_review?.user ? (
            <>
              <span className="highlight">{longest_review.words}</span> words by{" "}
              <strong>{longest_review.user}</strong> on &quot;<em>{longest_review.title}</em>&quot; →{" "}
              <a href={longest_review.url} target="_blank" rel="noopener noreferrer">
                Link
              </a>
            </>
          ) : (
            "No review data available."
          )}
        </p>

        <h2>Shortest Review</h2>
        <p>
          {shortest_review?.user ? (
            <>
              <span className="highlight">{shortest_review.words}</span> words by{" "}
              <strong>{shortest_review.user}</strong> on &quot;<em>{shortest_review.title}</em>&quot; →{" "}
              <a href={shortest_review.url} target="_blank" rel="noopener noreferrer">
                Link
              </a>
            </>
          ) : (
            "No review data available."
          )}
        </p>
      </div>
      <footer>&copy; 2025 Letterboxd Stats by Brandon Joubran</footer>
    </div>
  );
}
