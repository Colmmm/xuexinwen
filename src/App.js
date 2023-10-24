import './App.css';
import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams } from 'react-router-dom'; 
import ArticleComponent from './components/ArticleComponent';
import ArticlePreview from './components/ArticlePreview';

function App() {
  // State to store the list of article IDs
  const [articleIds, setArticleIds] = useState([]);

  // Fetch article IDs when the component mounts
  useEffect(() => {
    fetch('http://localhost:5000/api/article_ids')
      .then((response) => response.json())
      .then((data) => setArticleIds(data));
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home articleIds={articleIds} />} />
        <Route path="/article/:articleId" element={<ArticlePage />} />
      </Routes>
    </Router>
  );
}

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

function ArticlePage() {
  const { articleId } = useParams();

  return (
    <ArticleComponent key={articleId} articleId={articleId} />
  );
}

export default App;
