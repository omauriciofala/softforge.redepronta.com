import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const envDir = path.resolve(__dirname, "../../");
  const env = loadEnv(mode, envDir, "");
  const targetApi = env.VITE_API_BASE_URL || "http://127.0.0.1:8002";

  return {
    plugins: [react()],
    envDir,
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 5173,
      host: "0.0.0.0",
      proxy: {
        "/api": {
          target: targetApi,
          changeOrigin: true,
          ws: true,
        },
      },
    },
  };
});
