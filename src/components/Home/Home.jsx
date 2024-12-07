import { Link } from 'react-router-dom'
import ArticlePreview from '../ArticlePreview/ArticlePreview'
import Navbar from '../Navbar/Navbar'
import './Home.css'

function Home({ articles }) {
  return (
    <div>
      <Navbar />
      <div className="previews-container">
        {articles.map((article) => (
          <Link 
            to={`/article/${article.article_id}/grade/native`} 
            key={article.article_id}
            className="preview-link"
          >
            <ArticlePreview article={article} />
          </Link>
        ))}
      </div>
    </div>
  )
}

export default Home
