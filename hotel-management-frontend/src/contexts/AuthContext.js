// src/contexts/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from "react";
import { useNavigate } from "react-router-dom";  // useNavigate hook for navigation

const AuthContext = createContext();  // Create a context for user authentication

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);  // State to store user data
  const [loading, setLoading] = useState(true);  // Loading state while checking authentication
  const navigate = useNavigate();  // Hook for navigation

  // Function to check if the user is authenticated
  const checkAuth = async () => {
    try {
      // Check if user token is stored in localStorage
      const token = localStorage.getItem("token");

      if (!token) {
        setUser(null);  // No token means user is not authenticated
        setLoading(false);  // Stop loading
        return;
      }

      // You can add an API call here to validate the token or get the user info
      // For now, we assume the token is valid and set a mock user
      const mockUser = { username: "JohnDoe", role: "admin", password: "fcn", adminPassword: "pass" };  // Mock user (replace with API call)

      setUser(mockUser);  // Set the authenticated user
    } catch (error) {
      console.error("Error in authentication check:", error);
      setUser(null);  // If there's an error, treat user as not authenticated
    } finally {
      setLoading(false);  // Stop loading
    }
  };

  useEffect(() => {
    checkAuth();  // Check authentication when the app loads
  }, []);

  const login = (userData) => {
    // Assume successful login, store token in localStorage
    localStorage.setItem("token", userData.token);
    setUser(userData.user);  // Set the user data after successful login
    navigate("/dashboard");  // Redirect to dashboard after login
  };

  const logout = () => {
    // Clear user data and token
    localStorage.removeItem("token");
    setUser(null);
    navigate("/login");  // Redirect to login page
  };

  // Provide context values to all child components
  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to access the AuthContext in any component
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

