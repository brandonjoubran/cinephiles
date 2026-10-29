import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }) => (isActive ? "active" : undefined);

/** Stats page nav — same markup and classes as the old index.html. */
export default function StatsNav() {
  return (
    <nav className="stats-nav">
      <NavLink to="/" className="nav-brand" end>
        OnlyCinephiles
      </NavLink>
      <ul className="nav-links">
        <li>
          <NavLink to="/" end className={linkClass}>
            Stats
          </NavLink>
        </li>
        <li>
          <NavLink to="/watchlist" className={linkClass}>
            Watchlist
          </NavLink>
        </li>
        <li>
          <NavLink to="/meetings" className={linkClass}>
            Meetings
          </NavLink>
        </li>
        <li>
          <NavLink to="/leaderboard" className={linkClass}>
            Leaderboard
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}
