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
    allowedHosts: ['eventqr.app', 'www.eventqr.app', '172.105.189.124', 'localhost'],
    // Disable host check completely
    hmr: {
      overlay: false,
      host: 'eventqr.app'
    }
  },
  preview: {
    host: '0.0.0.0',
    strictPort: true,
    allowedHosts: ['eventqr.app', 'www.eventqr.app', '172.105.189.124', 'localhost']
  }
});
