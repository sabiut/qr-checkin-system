import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  base: '/',
  plugins: [tailwindcss(), tsconfigPaths()],
  server: {
    host: '0.0.0.0',
    strictPort: true,
    port: 3000
  },
  preview: {
    host: '0.0.0.0',
    strictPort: true,
    port: 3000
  }
});