import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';  // For navigation after successful login
import { loginUser } from '../api/users';  // Assume this function makes the API call for login
import './Login.css';  // Import your custom CSS for styling

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const token = await loginUser(username, password);  // Assume loginUser function makes the API call
      localStorage.setItem('token', token);  // Store the token in local storage for future requests
      navigate('/dashboard');  // Redirect to dashboard after successful login
    } catch (err) {
      setError('Invalid credentials, please try again.');
    }
    setLoading(false);
  };

  return (
    <div className="login-container">
      <h2>Login</h2>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleSubmit} className="login-form">
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
        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default Login;
