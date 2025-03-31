import { type RouteConfig, index } from "@react-router/dev/routes";

export default [
  // Public routes
  {
    path: "/",
    file: "routes/home.tsx",
  },
  {
    path: "login",
    file: "routes/login.tsx",
  },
  {
    path: "register",
    file: "routes/register.tsx",
  },
  // Protected routes that require authentication
  {
    path: "events/new",
    file: "routes/events.new.tsx",
  },
  {
    path: "events/:eventId",
    file: "routes/events.$eventId.tsx",
  },
  {
    path: "events/:eventId/check-in",
    file: "routes/events.$eventId.check-in.tsx",
  },
] satisfies RouteConfig;