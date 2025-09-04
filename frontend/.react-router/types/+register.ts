import "react-router";

declare module "react-router" {
  interface Register {
    params: Params;
  }
}

type Params = {
  "/": {};
  "/": {};
  "/login": {};
  "/register": {};
  "/contact": {};
  "/events": {};
  "/events/new": {};
  "/events/:eventId": {
    "eventId": string;
  };
  "/events/:eventId/check-in": {
    "eventId": string;
  };
  "/dashboard": {};
};