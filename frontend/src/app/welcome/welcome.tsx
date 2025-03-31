import React from 'react';

export function Welcome() {
  return React.createElement("div", { className: "min-h-screen bg-gray-50 flex items-center justify-center" },
    React.createElement("div", { className: "text-center" },
      React.createElement("h1", { className: "text-3xl font-bold text-gray-800 mb-4" }, "QR Check-in System"),
      React.createElement("p", { className: "text-gray-600 mb-8" }, "An easy way to manage events and track attendees"),
      React.createElement("div", { className: "flex justify-center gap-4" },
        React.createElement("a", { href: "/login", className: "px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors" }, "Sign In"),
        React.createElement("a", { href: "/register", className: "px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors" }, "Register")
      )
    )
  );
}
