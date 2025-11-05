import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";
import envCompatible from "vite-plugin-env-compatible";
import { createHtmlPlugin } from "vite-plugin-html";
import { nodePolyfills } from "vite-plugin-node-polyfills";
import progress from "vite-plugin-progress";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  optimizeDeps: {
    include: ["xlsx"],
  },
  plugins: [
    react(),
    tsconfigPaths(),
    nodePolyfills(),
    createHtmlPlugin({
      inject: {
        data: {
          title: "Data Canvas",
        },
      },
      template: "index.html",
    }),
    envCompatible(),
    progress(),
  ],
  build: {
    minify: "terser",
    terserOptions: {
      mangle: true,
    },
    sourcemap: true,
    rollupOptions: {
      output: {
        chunkFileNames: `[name].[hash].js`,
      },
    },
  },
  worker: {
    format: "es",
  },
  resolve: {
    alias: {
      "~": path.resolve(__dirname, "src"),
    },
  },
  server: {
    host: "0.0.0.0", // Ensure the server is accessible on all network interfaces
    port: 3000, // Set the port to 3000
    proxy: {
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
      },
    },
  },
});
