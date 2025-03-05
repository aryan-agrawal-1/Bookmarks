import React from 'react';
// handling redirects and nested routes.
import { Navigate, Outlet } from 'react-router-dom';

const ProtectedRoute = () => {
  // Retrieve the JWT access token from localStorage.
  // This token was stored on successful login.
  const token = localStorage.getItem('access');

  // If the token exists, the user is authenticated,
  // so render the nested child routes/components via <Outlet>.
  // Otherwise, redirect the user to the login page.
  return token ? <Outlet /> : <Navigate to="/login" replace />;
};

export default ProtectedRoute;
