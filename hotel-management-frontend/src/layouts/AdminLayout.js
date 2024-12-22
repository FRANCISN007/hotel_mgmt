import React from 'react';
import { Outlet } from 'react-router-dom'; // For rendering nested routes

const AdminLayout = () => (
  <div>
    <h1>Admin Dashboard</h1>
    {/* This will render nested routes */}
    <Outlet />
  </div>
);

export default AdminLayout;
