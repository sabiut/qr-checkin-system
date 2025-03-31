import type {
  LinksFunction as ReactRouterLinksFunction,
  ErrorBoundaryProps as ReactRouterErrorBoundaryProps,
  MetaFunctionArgs as ReactRouterMetaFunctionArgs,
  MetaFunction as ReactRouterMetaFunction,
} from "react-router";

export namespace Route {
  export type LinksFunction = ReactRouterLinksFunction;
  export type ErrorBoundaryProps = ReactRouterErrorBoundaryProps;
  export type MetaArgs = ReactRouterMetaFunctionArgs;
  export type MetaFunction = ReactRouterMetaFunction;
}