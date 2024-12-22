import React, { createContext, useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const navigate = useNavigate(); // Now valid because AuthProvider is inside Router

  const login = (userData) => {
    setUser(userData);
    navigate('/dashboard'); // Example: Redirect to dashboard on login
  };

  const logout = () => {
    setUser(null);
    navigate('/login'); // Example: Redirect to login on logout
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
