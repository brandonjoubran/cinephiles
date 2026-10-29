import { useEffect, useState } from "react";
import ClubNav from "../components/ClubNav.jsx";
import { getLeaderboardPage } from "../api/client.js";
import "../styles/leaderboard.css";

export default function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getLeaderboardPage()
      .then((data) => setLeaderboard(data.leaderboard))
      .catch((err) => setError(err.message));
  }, []);

  const entries = leaderboard ? Object.entries(leaderboard) : [];

  return (
    <div className="page-shell--leaderboard">
      <ClubNav />
      <div className="container card">
      <header className="top">
        <h1>🏆 Leaderboard</h1>
        <div className="hint">Ordered most → least</div>
      </header>

      <div className="board">
        {error ? <div className="empty">Error: {error}</div> : null}
        {!leaderboard && !error ? <div className="empty">Loading…</div> : null}
        {entries.length > 0 ? (
          <ul className="list" role="list">
            {entries.map(([username, score], index) => {
              const rank = index + 1;
              const topClass = rank === 1 ? "top1" : rank === 2 ? "top2" : rank === 3 ? "top3" : "";
              return (
                <li className={`item ${topClass}`} key={username}>
                  {rank > 3 ? <div className="rank default">{rank}</div> : null}
                  <div className="user">
                    {rank <= 3 ? (
                      <div className="medal" aria-hidden="true">
                        {rank === 1 ? "🥇" : rank === 2 ? "🥈" : "🥉"}
                      </div>
                    ) : null}
                    <div className="meta">
                      <div className="username">
                        <a
                          href={
                            score > 0
                              ? `https://letterboxd.com/${username}/diary/for/2026/`
                              : `https://letterboxd.com/${username}/`
                          }
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {username}
                        </a>
                      </div>
                      <div className="sub">
                        {score} movie{score === 1 ? "" : "s"}
                      </div>
                    </div>
                  </div>
                  <div className="score">{score}</div>
                </li>
              );
            })}
          </ul>
        ) : leaderboard ? (
          <div className="empty">No leaderboard data found.</div>
        ) : null}
      </div>
      </div>
    </div>
  );
}
