import React, { useState } from 'react';
import { registerUser } from '../api/users'; // Assume this function makes the API call for registration
import './Register.css'; // Import your custom CSS for styling

const Register = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [adminPassword, setAdminPassword] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    // Frontend validation for admin password
    if (role === 'admin' && !adminPassword.trim()) {
      setError('Admin password is required for admin registration.');
      setLoading(false);
      return;
    }

    try {
      // API Call: Ensure registerUser matches the backend requirements
      await registerUser({
        username,
        password,
        role,
        admin_password: role === 'admin' ? adminPassword : null,
    });
    
      setSuccess(true);
      setLoading(false);

      // Clear form fields after successful registration
      setUsername('');
      setPassword('');
      setRole('user');
      setAdminPassword('');
    } catch (err) {
      // Capture backend error messages if available
      const backendError = err.response?.data?.detail || 'Error registering user. Please try again.';
      setError(backendError);
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <h2>Register</h2>
      {error && <p className="error">{error}</p>}
      {success && <p className="success">Registration successful! You can now log in.</p>}
      <form onSubmit={handleSubmit} className="register-form">
        <div className="input-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div className="input-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div className="input-group">
          <label htmlFor="role">Role</label>
          <select
            id="role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        {role === 'admin' && (
          <div className="input-group">
            <label htmlFor="adminPassword">Admin Password</label>
            <input
              type="password"
              id="adminPassword"
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
              required
            />
          </div>
        )}
        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
    </div>
  );
};

export default Register;
