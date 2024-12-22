import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => (
  <nav>
    <ul>
      <li><Link to="/">Home</Link></li>
      <li><Link to="/rooms">Rooms</Link></li>
      <li><Link to="/bookings">Bookings</Link></li>
      <li><Link to="/payments">Payments</Link></li>
      <li><Link to="/login">Login</Link></li>
    </ul>
  </nav>
);

export default Navbar;
