// src/pages/LoginPage.js
import React, { useState } from "react";
import { useAuth } from "contexts/AuthContext"; // Access AuthContext

const LoginPage = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const { login } = useAuth(); // Access the login function from AuthContext

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); // Clear any previous error

    if (!username || !password) {
      setError("Please enter both username and password.");
      return;
    }

    setLoading(true);
    try {
      await login(username, password); // Call login with username and password
    } catch {
      setError("Invalid username or password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <form onSubmit={handleSubmit} style={styles.form}>
        <h2>Login</h2>
        {error && <div style={styles.error}>{error}</div>}
        <div style={styles.inputGroup}>
          <label htmlFor="username" style={styles.label}>
            Username:
          </label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your username"
            required
            style={styles.input}
          />
        </div>
        <div style={styles.inputGroup}>
          <label htmlFor="password" style={styles.label}>
            Password:
          </label>
          <div style={styles.passwordContainer}>
            <input
              type={showPassword ? "text" : "password"}
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              style={styles.input}
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              style={styles.toggleButton}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>
        </div>
        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
    </div>
  );
};

// Inline styles for the component
const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100vh",
    backgroundColor: "#f4f4f4",
    padding: "1rem",
  },
  form: {
    backgroundColor: "#fff",
    padding: "2rem",
    borderRadius: "8px",
    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
    width: "100%",
    maxWidth: "400px",
  },
  inputGroup: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: "1rem",
  },
  label: {
    flex: "0 0 30%", // Adjust the width of the label
    textAlign: "right",
    marginRight: "1rem",
    fontWeight: "bold",
  },
  input: {
    flex: "1",
    padding: "0.5rem",
    border: "1px solid #ddd",
    borderRadius: "4px",
  },
  passwordContainer: {
    display: "flex",
    alignItems: "center",
    flex: "1",
  },
  toggleButton: {
    marginLeft: "0.5rem",
    backgroundColor: "transparent",
    border: "none",
    color: "#007bff",
    cursor: "pointer",
    fontSize: "0.9rem",
  },
  button: {
    backgroundColor: "#007bff",
    color: "#fff",
    border: "none",
    padding: "0.5rem 1rem",
    borderRadius: "4px",
    cursor: "pointer",
    width: "100%",
    marginTop: "1rem",
  },
  error: {
    color: "red",
    marginBottom: "1rem",
    fontSize: "0.9rem",
  },
};

export default LoginPage;
