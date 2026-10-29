import { useCallback, useEffect, useState } from "react";
import ClubNav from "../components/ClubNav.jsx";
import { addMeeting, getMeetingsPage } from "../api/client.js";
import "../styles/meetings.css";

export default function MeetingsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedParticipants, setSelectedParticipants] = useState([]);
  const [form, setForm] = useState({
    movie_slug: "",
    date: new Date().toISOString().slice(0, 10),
    start_time: "19:00",
    end_time: "22:00",
  });

  const load = useCallback(async () => {
    try {
      setError(null);
      const page = await getMeetingsPage();
      setData(page);
      if (page.selected_movies?.length && !form.movie_slug) {
        setForm((f) => ({ ...f, movie_slug: page.selected_movies[0].SLUG }));
      }
    } catch (err) {
      setError(err.message);
    }
  }, [form.movie_slug]);

  useEffect(() => {
    load();
  }, [load]);

  const addParticipant = (username) => {
    if (!username || selectedParticipants.includes(username)) return;
    setSelectedParticipants((prev) => [...prev, username]);
  };

  const removeParticipant = (username) => {
    setSelectedParticipants((prev) => prev.filter((u) => u !== username));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    try {
      await addMeeting({
        ...form,
        participants: selectedParticipants.join(", "),
      });
      setModalOpen(false);
      setSelectedParticipants([]);
      await load();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="page-shell--wide">
      <ClubNav />
      <div className="container">
        <div className="header">
          <div className="header-title">🗓️ Club Meetings</div>
          <div style={{ display: "flex", gap: "12px", flexDirection: "row" }}>
            <button type="button" className="add-movie-btn" onClick={() => setModalOpen(true)}>
              +
            </button>
          </div>
        </div>

        {error ? <p>Error: {error}</p> : null}

        <table>
          <tbody>
            {(data?.meetings || []).map((meeting) => (
              <tr className="meeting-row" key={`${meeting.DATE}-${meeting.MOVIE_SLUG}`}>
                <td colSpan={5} style={{ paddingBottom: "6px" }}>
                  <div className="header-title" style={{ fontWeight: "bold", fontSize: "1.5em", marginBottom: "6px" }}>
                    {meeting.DATE} -{" "}
                    {meeting.MOVIE_SLUG ? (
                      <a
                        className="movie-link"
                        href={`https://letterboxd.com/film/${meeting.MOVIE_SLUG}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {meeting.MOVIE_NAME}
                      </a>
                    ) : (
                      meeting.MOVIE_NAME
                    )}
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "18px", fontSize: "0.98em" }}>
                    <span>
                      <strong>Start:</strong> {meeting.START_TIME}
                    </span>
                    <span>
                      <strong>End:</strong> {meeting.END_TIME}
                    </span>
                    <span>
                      <strong>Duration:</strong> {meeting.DURATION}
                    </span>
                    <span>
                      <strong>Participants:</strong> {meeting.PARTICIPANTS}
                    </span>
                    <span>
                      <strong>ROTW:</strong> {meeting.ROTW || "—"}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalOpen ? (
        <div className="modal-overlay" style={{ display: "flex" }} onClick={() => setModalOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={onSubmit}>
              <h3 style={{ marginTop: 0 }}>Add Meeting</h3>
              <label>Select movie:</label>
              <select
                name="movie_slug"
                required
                style={{ width: "100%", marginBottom: "12px" }}
                value={form.movie_slug}
                onChange={(e) => setForm((f) => ({ ...f, movie_slug: e.target.value }))}
              >
                {(data?.selected_movies || []).map((movie) => (
                  <option key={movie.SLUG} value={movie.SLUG}>
                    {movie.TITLE}
                  </option>
                ))}
              </select>
              <label>Date:</label>
              <input
                type="date"
                name="date"
                required
                style={{ width: "100%", marginBottom: "12px" }}
                value={form.date}
                onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
              />
              <label>Start time:</label>
              <input
                type="time"
                name="start_time"
                required
                style={{ width: "100%", marginBottom: "12px" }}
                value={form.start_time}
                onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))}
              />
              <label>End time:</label>
              <input
                type="time"
                name="end_time"
                required
                style={{ width: "100%", marginBottom: "12px" }}
                value={form.end_time}
                onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))}
              />
              <label>Participants:</label>
              <select
                style={{ width: "100%", marginBottom: "8px" }}
                defaultValue=""
                onChange={(e) => {
                  addParticipant(e.target.value);
                  e.target.value = "";
                }}
              >
                <option value="" disabled>
                  Select a username
                </option>
                {(data?.usernames || []).map((username) => (
                  <option key={username} value={username}>
                    {username}
                  </option>
                ))}
              </select>
              <div style={{ marginBottom: "12px" }}>
                {selectedParticipants.map((username) => (
                  <span
                    key={username}
                    style={{
                      display: "inline-block",
                      marginRight: "8px",
                      background: "#e0f7fa",
                      padding: "2px 8px",
                      borderRadius: "12px",
                    }}
                  >
                    {username}{" "}
                    <button type="button" onClick={() => removeParticipant(username)}>
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
                <button type="button" className="close-btn" onClick={() => setModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="submit-btn">
                  Add
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}
