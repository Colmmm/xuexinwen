import React, { useState, useEffect } from 'react';

const ArticlePreview = ({ articleId }) => {
  const [articleData, setArticleData] = useState(null);

  useEffect(() => {
    // Fetch article data based on articleId
    fetch(`http://localhost:5000/api/articles/${articleId}`)
      .then((response) => response.json())
      .then((data) => setArticleData(data))
      .catch((error) => console.error('Error fetching article:', error));
  }, [articleId]);

  return (
    <div className="article-preview">
      {articleData && (
        <div>
          <img src={articleData.images[0]}/>
          <h2>{articleData.title}</h2>
          <p>{articleData.simplified_text}</p>
        </div>
      )}
    </div>
  );
};

export default ArticlePreview;