import './Home.css';
import ArticlePreview from "../ArticlePreview/ArticlePreview";
import {Link} from 'react-router-dom';
import Navbar from '../Navbar/Navbar'; // Import the Navbar component 



function Home({ articleIds }) {
    return (
      <div>
        <Navbar />
        <div className="previews-container">
          {articleIds.map((articleId) => (
            <Link to={`/article/${articleId}`} key={articleId}>
              <ArticlePreview key={articleId} articleId={articleId} />
            </Link>
          ))}
        </div>
      </div>
    );
  }


export default Home;