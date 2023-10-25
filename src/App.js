import './App.css';
import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useParams } from 'react-router-dom'; 
import ArticleComponent from './components/ArticleComponent/ArticleComponent';
import Home from './components/Home/Home';

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
        {articleIds.map((articleId) => (
          <Route key={articleId} path={`/article/${articleId}`} element={<ArticleComponent articleId={articleId} />} />
        ))}
      </Routes>
    </Router>
  );
}


export default App;
