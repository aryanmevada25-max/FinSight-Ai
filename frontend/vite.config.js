import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "/static/dist/",
  build: {
    outDir: "../static/dist",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: "src/main.jsx",
    },
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/app": "http://127.0.0.1:5000",
    },
  },
});
