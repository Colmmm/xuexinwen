import './App.css';
import React, { useEffect, useState } from 'react';
//import ArticleComponent from './components/ArticleComponent';
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
    <div>
      <h1>Article Previews</h1>
      <div className="previews-container">
        {articleIds.map((articleId) => (
          <ArticlePreview key={articleId} articleId={articleId} />
        ))}
      </div>
    </div>
  );
}

export default App;
