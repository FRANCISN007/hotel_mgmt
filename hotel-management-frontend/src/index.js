// index.js
import React from "react";
import { createRoot } from "react-dom/client"; // Import createRoot
import { BrowserRouter as Router } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import App from "./App";

// Get the root element
const rootElement = document.getElementById("root");

// Create the root and render the app
const root = createRoot(rootElement);
root.render(
  <React.StrictMode>
    <Router>
      <AuthProvider>
        <App />
      </AuthProvider>
    </Router>
  </React.StrictMode>
);
