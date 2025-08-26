import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  console.log('ProtectedRoute - loading:', loading, 'isAuthenticated:', isAuthenticated(), 'user:', user, 'location:', location.pathname);

  // Wait for auth state to initialize before making decisions
  if (loading) {
    return <div>Loading...</div>; // Or your loading component
  }

  if (!isAuthenticated()) {
    console.log('User not authenticated, redirecting to login');
    // Redirect to login page with return url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  console.log('User authenticated, rendering protected content');
  return children;
};

export default ProtectedRoute;
