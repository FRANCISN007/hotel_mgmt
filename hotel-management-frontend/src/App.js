// App.js
import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext"; // Import the AuthContext
import UserList from './components/UserList';  // Import the UserList component

// Import your pages and components
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register"; // Add if needed
import PrivateRoute from "./components/PrivateRoute";

// Home component for demonstration
function Home() {
  return <h1>Welcome to the Hotel Management System</h1>;
}

// Main App component
function App() {
  const { user, loading, logout } = useAuth();

  // Conditional rendering for loading state
  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div className="App">
      {/* Navigation Links */}
      <nav>
        <Link to="/">Home</Link>
        {!user ? (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        ) : (
          <>
            <Link to="/dashboard">Dashboard</Link>
            <button onClick={logout}>Logout</button>
          </>
        )}
      </nav>

      {/* Define Routes */}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Dashboard />
            </PrivateRoute>
          }
        />
      </Routes>
    </div>
  );
}

export default App;
