import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
export default defineConfig(({ mode }) => {
  const integratedTarget =
    process.env.INTEGRATED_API_TARGET ||
    loadEnv(mode, process.cwd(), "INTEGRATED_").INTEGRATED_API_TARGET ||
    "http://127.0.0.1:8010";
  if (!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(integratedTarget)) {
    throw new Error(
      "Integrated API target must be a local loopback HTTP address",
    );
  }
  return {
    plugins: [react(), tailwindcss()],
    server: {
      host: "127.0.0.1",
      proxy: {
        "/api": "http://127.0.0.1:8000",
        "/operations-api": {
          target: integratedTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/operations-api/, ""),
        },
      },
    },
    build: {
      rollupOptions: {
        input: {
          pack: "index.html",
          operations: "operations.html",
          shop: "shop.html",
        },
      },
    },
  };
});
