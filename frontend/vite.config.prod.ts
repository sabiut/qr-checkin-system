import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  base: '/',
  plugins: [tailwindcss(), tsconfigPaths()],
  server: {
    host: '0.0.0.0',
    strictPort: true,
    port: 3000,
    allowedHosts: ['eventqr.app', 'www.eventqr.app', '172.105.189.124', 'localhost']
  },
  preview: {
    host: '0.0.0.0',
    strictPort: true,
    port: 3000,
    allowedHosts: ['eventqr.app', 'www.eventqr.app', '172.105.189.124', 'localhost']
  }
});