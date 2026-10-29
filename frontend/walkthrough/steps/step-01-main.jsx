/**
 * STEP 1 — Entry point
 * Vite loads index.html → this file → mounts <App /> into #root
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);
