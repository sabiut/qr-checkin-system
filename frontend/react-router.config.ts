import type { Config } from "@react-router/dev/config";

export default {
  // Temporarily disable SSR to fix production build issues
  ssr: false,
  
  // Relative path prefix for app routes
  basename: "/",
  
  // Define app root directory
  appDirectory: "src/app",
  
  // Define route file
  routesFile: "routes.ts",
  
  // Define output directory
  outDir: "build",
} satisfies Config;