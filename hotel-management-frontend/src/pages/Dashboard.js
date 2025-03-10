// src/pages/DashboardPage.js
import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const DashboardPage = () => {
  const { user, logout } = useAuth();

  if (!user) {
    return <div>You are not logged in.</div>;
  }

  return (
    <div>
      <h1>Welcome, {user.username}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

export default DashboardPage;
