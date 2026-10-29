import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }) => (isActive ? "active" : undefined);

/**
 * Shared top navigation — rendered once in Layout.jsx for every page.
 */
export default function AppNav() {
  return (
    <nav className="app-nav">
      <NavLink to="/" className="app-nav__brand" end>
        OnlyCinephiles
      </NavLink>
      <ul className="app-nav__links">
        <li>
          <NavLink to="/" end className={linkClass}>
            📊 Stats
          </NavLink>
        </li>
        <li>
          <NavLink to="/watchlist" className={linkClass}>
            🎬 Watchlist
          </NavLink>
        </li>
        <li>
          <NavLink to="/meetings" className={linkClass}>
            📅 Meetings
          </NavLink>
        </li>
        <li>
          <NavLink to="/leaderboard" className={linkClass}>
            🏆 Leaderboard
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}
