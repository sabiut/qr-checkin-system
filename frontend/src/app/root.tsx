import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router";

import type { Route } from "./+types/root";
import "./app.css";
import SyncStatus from "./components/SyncStatus";
import NavBar from "./components/NavBar";
import { AuthProvider } from "./context/AuthContext";

export const links: Route.LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  {
    rel: "preconnect",
    href: "https://fonts.gstatic.com",
    crossOrigin: "anonymous",
  },
  {
    rel: "stylesheet",
    href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
  },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  try {
    // Detect browser environment
    const isBrowser = typeof window !== 'undefined';
    
    // Simple component to render during SSR before client-side hydration
    if (!isBrowser) {
      return (
        <div className="flex items-center justify-center bg-gray-50 py-4">
          <div className="text-center">
            <h1 className="text-base font-semibold text-gray-800">QR Check-in System</h1>
            <p className="text-xs text-gray-500">Loading...</p>
          </div>
        </div>
      );
    }
    
    return (
      <AuthProvider>
        <NavBar />
        <main>
          <Outlet />
          <SyncStatus />
        </main>
      </AuthProvider>
    );
  } catch (error) {
    console.error("Error in App component:", error);
    return (
      <div className="flex items-center justify-center bg-gray-50 py-4">
        <div className="text-center">
          <h1 className="text-base font-semibold text-red-600">Application Error</h1>
          <p className="text-xs text-gray-600">Error loading the application</p>
          <p className="text-xs text-gray-500 mt-1">{error instanceof Error ? error.message : String(error)}</p>
          <button 
            className="mt-2 bg-blue-600 text-white px-2 py-1 text-xs rounded"
            onClick={() => window.location.reload()}
          >
            Reload
          </button>
        </div>
      </div>
    );
  }
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Oops!";
  let details = "An unexpected error occurred.";
  let stack: string | undefined;

  console.error("Error caught by ErrorBoundary:", error);

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "404" : "Error";
    details =
      error.status === 404
        ? "The requested page could not be found."
        : error.statusText || details;
    console.error("Route error response:", { status: error.status, statusText: error.statusText });
  } else if (error instanceof Error) {
    details = error.message;
    stack = error.stack;
    console.error("Error instance:", { message: error.message, stack: error.stack });
  } else {
    console.error("Unknown error type:", error);
  }

  return (
    <main className="pt-16 p-4 container mx-auto">
      <h1 className="text-2xl font-bold mb-4">{message}</h1>
      <p className="mb-4">{details}</p>
      {stack && (
        <div className="bg-gray-100 p-4 rounded-lg mt-4">
          <h3 className="font-medium mb-2">Stack Trace:</h3>
          <pre className="w-full p-4 overflow-x-auto text-sm bg-gray-800 text-white rounded">
            <code>{stack}</code>
          </pre>
        </div>
      )}
      <div className="mt-6">
        <a 
          href="/"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Return to Home
        </a>
      </div>
    </main>
  );
}