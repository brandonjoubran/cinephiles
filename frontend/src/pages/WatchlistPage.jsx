import { useCallback, useEffect, useState } from "react";
import ClubNav from "../components/ClubNav.jsx";
import MovieCard from "../components/MovieCard.jsx";
import {
  addMovie,
  completeMovie,
  deleteMovie,
  generateNominators,
  getWatchlistPage,
  markUnwatched,
  markWatched,
  nominateMovie,
  selectMovie,
  voteMovie,
} from "../api/client.js";
import "../styles/watchlist.css";

function Modal({ open, onClose, children }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

export default function WatchlistPage() {
  const [movies, setMovies] = useState([]);
  const [usernames, setUsernames] = useState([]);
  const [error, setError] = useState(null);

  const [addOpen, setAddOpen] = useState(false);
  const [generateOpen, setGenerateOpen] = useState(false);
  const [nominateOpen, setNominateOpen] = useState(false);
  const [voteOpen, setVoteOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [selectOpen, setSelectOpen] = useState(false);
  const [completeOpen, setCompleteOpen] = useState(false);

  const [activeSlug, setActiveSlug] = useState("");
  const [addUrl, setAddUrl] = useState("");
  const [addUser, setAddUser] = useState("");
  const [actionUser, setActionUser] = useState("");
  const [voters, setVoters] = useState(null);
  const [rotwUsers, setRotwUsers] = useState([]);

  const load = useCallback(async () => {
    try {
      setError(null);
      const data = await getWatchlistPage();
      setMovies(data.movies);
      setUsernames(data.usernames);
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const runGenerate = async () => {
    setVoters(null);
    setGenerateOpen(true);
    try {
      const data = await generateNominators();
      setTimeout(() => setVoters(data.nominators || []), 1200);
    } catch (err) {
      setVoters([err.message]);
    }
  };

  const toggleRotw = (username) => {
    setRotwUsers((prev) =>
      prev.includes(username) ? prev.filter((u) => u !== username) : [...prev, username]
    );
  };

  const onAddMovie = async (e) => {
    e.preventDefault();
    try {
      await addMovie(addUrl, addUser);
      setAddOpen(false);
      setAddUrl("");
      await load();
    } catch (err) {
      alert(err.message);
    }
  };

  const onNominate = async (e) => {
    e.preventDefault();
    await nominateMovie(activeSlug, actionUser);
    setNominateOpen(false);
    await load();
  };

  const onVote = async (e) => {
    e.preventDefault();
    await voteMovie(activeSlug, actionUser);
    setVoteOpen(false);
    await load();
  };

  const onDelete = async (e) => {
    e.preventDefault();
    await deleteMovie(activeSlug);
    setDeleteOpen(false);
    await load();
  };

  const onSelect = async (e) => {
    e.preventDefault();
    await selectMovie(activeSlug);
    setSelectOpen(false);
    await load();
  };

  const onComplete = async (e) => {
    e.preventDefault();
    if (rotwUsers.length === 0) {
      const ok = window.confirm("Are you sure you want to leave 'Review of the Week' blank?");
      if (!ok) return;
    }
    await completeMovie(activeSlug, rotwUsers);
    setCompleteOpen(false);
    setRotwUsers([]);
    await load();
  };

  return (
    <div className="page-shell--wide">
      <ClubNav />
      <div className="logo-container">
        <img src="/logo.png" alt="Watchlist Logo" className="logo" />
      </div>
      <div className="header">
        <div className="header-title">🍿 Watchlist</div>
        <div style={{ display: "flex", gap: "12px", flexDirection: "row" }}>
          <button type="button" className="generate-voters-btn" onClick={runGenerate}>
            🎲
          </button>
          <button type="button" className="add-movie-btn" onClick={() => setAddOpen(true)}>
            +
          </button>
        </div>
      </div>

      {error ? <p style={{ color: "red" }}>Error: {error}</p> : null}

      <div className="card-container">
        {movies.map((movie) => (
          <MovieCard
            key={movie.SLUG}
            movie={movie}
            onDelete={(slug) => {
              setActiveSlug(slug);
              setDeleteOpen(true);
            }}
            onNominate={(slug) => {
              setActiveSlug(slug);
              setNominateOpen(true);
            }}
            onVote={(slug) => {
              setActiveSlug(slug);
              setVoteOpen(true);
            }}
            onSelect={(slug) => {
              setActiveSlug(slug);
              setSelectOpen(true);
            }}
            onComplete={(slug) => {
              setActiveSlug(slug);
              setRotwUsers([]);
              setCompleteOpen(true);
            }}
            onMarkWatched={async (slug) => {
              await markWatched(slug);
              await load();
            }}
            onMarkUnwatched={async (slug) => {
              await markUnwatched(slug);
              await load();
            }}
            onRemoveNomination={async (slug) => {
              const m = movies.find((x) => x.SLUG === slug);
              if (m?.NOMINATED_BY) await nominateMovie(slug, m.NOMINATED_BY);
              await load();
            }}
          />
        ))}
      </div>

      <Modal open={addOpen} onClose={() => setAddOpen(false)}>
        <h2>Add a Movie</h2>
        <form onSubmit={onAddMovie}>
          <label htmlFor="movie-link">Enter a Letterboxd link:</label>
          <input
            id="movie-link"
            value={addUrl}
            onChange={(e) => setAddUrl(e.target.value)}
            placeholder="Enter Letterboxd link..."
            required
          />
          <label htmlFor="user-select">Choose a user:</label>
          <select id="user-select" value={addUser} onChange={(e) => setAddUser(e.target.value)} required>
            <option value="" disabled>
              Select your username
            </option>
            {usernames.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
          <div className="modal-actions">
            <button type="button" className="close-btn" onClick={() => setAddOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Add Movie
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={generateOpen} onClose={() => setGenerateOpen(false)}>
        <h2>Nominees!</h2>
        <div
          id="randomUsersList"
          className="dice-loader voter-results"
          style={{ flexDirection: voters ? "column" : "row" }}
        >
          {!voters ? (
            <>
              <div className="die">🎲</div>
              <div className="die">🎲</div>
              <div className="die">🎲</div>
            </>
          ) : (
            voters.map((voter) => (
              <p className="die reveal" key={voter}>
                {voter}
              </p>
            ))
          )}
        </div>
        <div className="modal-actions">
          <button type="button" className="close-btn" onClick={() => setGenerateOpen(false)}>
            Close
          </button>
        </div>
      </Modal>

      <Modal open={nominateOpen} onClose={() => setNominateOpen(false)}>
        <h2>Nominate Movie</h2>
        <form onSubmit={onNominate}>
          <select value={actionUser} onChange={(e) => setActionUser(e.target.value)} required>
            <option value="" disabled>
              Select your username
            </option>
            {usernames.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
          <div className="modal-actions">
            <button type="button" className="close-btn" onClick={() => setNominateOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Nominate
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={voteOpen} onClose={() => setVoteOpen(false)}>
        <h2>Vote Movie</h2>
        <form onSubmit={onVote}>
          <select value={actionUser} onChange={(e) => setActionUser(e.target.value)} required>
            <option value="" disabled>
              Select your username
            </option>
            {usernames.map((u) => (
              <option key={u} value={u}>
                {u}
              </option>
            ))}
          </select>
          <div className="modal-actions">
            <button type="button" className="close-btn" onClick={() => setVoteOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Vote
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <h2>Confirm Deletion</h2>
        <p>Are you sure you want to delete this movie?</p>
        <form onSubmit={onDelete}>
          <div className="modal-actions">
            <button type="button" className="close-btn" onClick={() => setDeleteOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Delete
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={selectOpen} onClose={() => setSelectOpen(false)}>
        <h2>Confirm Selection</h2>
        <p>Are you sure you want to select this as the winning movie?</p>
        <form onSubmit={onSelect}>
          <div className="modal-actions">
            <button type="button" className="close-btn" onClick={() => setSelectOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Confirm
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={completeOpen} onClose={() => setCompleteOpen(false)}>
        <h2>Confirm Selection</h2>
        <p>Are you sure you want to mark this movie as watched? It will reset the data for the week.</p>
        <form onSubmit={onComplete}>
          <div className="review-of-week-section">
            <h3>Review of the Week?</h3>
            <p>Select users who will win &quot;Review of the Week&quot;:</p>
            <select
              className="review-dropdown"
              defaultValue=""
              onChange={(e) => {
                if (e.target.value) toggleRotw(e.target.value);
                e.target.value = "";
              }}
            >
              <option value="" disabled>
                Select a username
              </option>
              {usernames.map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
            <div className="selected-users-list">
              {rotwUsers.map((u) => (
                <div className="selected-user" key={u} data-username={u}>
                  <span>{u}</span>
                  <button type="button" onClick={() => toggleRotw(u)}>
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div className="modal-actions">
            <button type="button" className="close-btn" onClick={() => setCompleteOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Confirm
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
