import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev (`vite`), the backend runs on port 8000. These proxies make the
// React app call relative URLs like /wallets/1 and Vite forwards them to
// the backend — same behaviour as production, where FastAPI serves both
// the built frontend and the API from a single origin.
const backend = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "127.0.0.1",
    proxy: {
      "/wallets": backend,
      "/loans": backend,
      "/users": backend,
      "/ask": backend,
      "/health": backend,
    },
  },
});
