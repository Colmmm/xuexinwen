import { Link } from 'react-router-dom'
import './Navbar.css'

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar--container">
        <Link to="/" className="navbar--brand">
          <img src="/XXW_Banner.png" alt="Xue Xinwen" className="navbar--logo" />
        </Link>
        <div className="navbar--description">
          Learn Chinese through News
        </div>
      </div>
    </nav>
  )
}

export default Navbar
