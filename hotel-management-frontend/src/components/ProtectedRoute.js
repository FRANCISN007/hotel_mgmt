
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '..../contexts/AuthContext';



const ProtectedRoute = ({ children }) => {
    const { user } = useAuth();
  
    if (!user) {
      return <Navigate to="/login" />;  // Redirect to login if not authenticated
    }
  
    return children;  // Render children if authenticated
  };
  
  export default ProtectedRoute;