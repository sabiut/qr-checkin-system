import type {
  MetaFunctionArgs as ReactRouterMetaFunctionArgs,
  MetaFunction as ReactRouterMetaFunction,
} from "react-router";

export namespace Route {
  export type MetaArgs = ReactRouterMetaFunctionArgs;
  export type MetaFunction = ReactRouterMetaFunction;
}