import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }) => `nav-item${isActive ? " active" : ""}`;

/** Watchlist, Meetings, and Leaderboard nav — emoji links and blue active pill. */
export default function ClubNav() {
  return (
    <nav className="navbar">
      <div className="nav-container">
        <NavLink to="/" end className={linkClass}>
          📊 Stats
        </NavLink>
        <NavLink to="/watchlist" className={linkClass}>
          🎬 Watchlist
        </NavLink>
        <NavLink to="/meetings" className={linkClass}>
          📅 Meetings
        </NavLink>
        <NavLink to="/leaderboard" className={linkClass}>
          🏆 Leaderboard
        </NavLink>
      </div>
    </nav>
  );
}
