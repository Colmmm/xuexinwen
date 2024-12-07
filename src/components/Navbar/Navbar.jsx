import { Link } from 'react-router-dom'
import './Navbar.css'

const Navbar = () => {
  return (
    <nav className="navbar">
      <div className="navbar--container">
        <Link to="/" className="navbar--brand">
          学新闻 <span className="navbar--brand-en">Xue Xinwen</span>
        </Link>
        <div className="navbar--description">
          Learn Chinese through News
        </div>
      </div>
    </nav>
  )
}

export default Navbar
