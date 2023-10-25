import React from 'react';
import { Link } from 'react-router-dom';
import "./Navbar.css";

function Navbar() {
  return (
    <nav className="navbar">
      <div className="logo">
        <Link to="/">
          <span className='logo--text'>Xue-新聞</span>
        </Link>
      </div>
    </nav>
  );
}

export default Navbar;