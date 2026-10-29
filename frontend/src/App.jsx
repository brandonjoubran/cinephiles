import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import StatsPage from "./pages/StatsPage.jsx";
import WatchlistPage from "./pages/WatchlistPage.jsx";
import MeetingsPage from "./pages/MeetingsPage.jsx";
import LeaderboardPage from "./pages/LeaderboardPage.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<StatsPage />} />
        <Route path="/watchlist" element={<WatchlistPage />} />
        <Route path="/meetings" element={<MeetingsPage />} />
        <Route path="/leaderboard" element={<LeaderboardPage />} />
      </Route>
    </Routes>
  );
}
