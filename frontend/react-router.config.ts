import type { Config } from "@react-router/dev/config";

export default {
  // Enable Server-side rendering for better SEO and performance
  ssr: true,
  
  // Relative path prefix for app routes
  basename: "/",
  
  // Define app root directory
  appDirectory: "src/app",
  
  // Define route file
  routesFile: "routes.ts",
  
  // Define output directory
  outDir: "build",
} satisfies Config;