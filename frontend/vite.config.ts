import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Dummy

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    host: true,
    port: 5173,
    allowedHosts: [".ngrok-free.dev", ".ngrok-free.app"],
  },
});
