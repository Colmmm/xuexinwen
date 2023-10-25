import './Home.css';
import ArticlePreview from "./ArticlePreview";
import {Link} from 'react-router-dom'; 


function Home({ articleIds }) {
    return (
      <div>
        <h1>Article Previews</h1>
        <nav>
          <Link to="/">Home</Link>
        </nav>
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