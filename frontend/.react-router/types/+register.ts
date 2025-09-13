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
  "/rsvp/:invitationId": {
    "invitationId": string;
  };
  "/icebreaker/:token": {
    "token": string;
  };
  "/events": {};
  "/events/new": {};
  "/events/:eventId": {
    "eventId": string;
  };
  "/events/:eventId/check-in": {
    "eventId": string;
  };
  "/events/:eventId/communication": {
    "eventId": string;
  };
  "/dashboard": {};
  "/profile": {};
  "/settings": {};
};