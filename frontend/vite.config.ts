import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  base: '/',
  plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
  server: {
    host: '0.0.0.0',
    strictPort: true,
    // Disable host check completely
    hmr: {
      overlay: false,
      host: 'eventqr.app'
    }
  },
  preview: {
    host: '0.0.0.0',
    strictPort: true
  }
});
