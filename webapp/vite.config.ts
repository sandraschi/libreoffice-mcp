import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 10983,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api": { target: "http://127.0.0.1:10981", changeOrigin: true },
      "/health": { target: "http://127.0.0.1:10981", changeOrigin: true },
      "/docs": { target: "http://127.0.0.1:10981", changeOrigin: true },
      "/openapi.json": { target: "http://127.0.0.1:10981", changeOrigin: true },
      "/redoc": { target: "http://127.0.0.1:10981", changeOrigin: true },
    },
  },
});
