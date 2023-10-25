import React, { useState, useEffect } from 'react';
import './ArticlePreview.css'; // Import the CSS file

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
    <div >
      {articleData && (
        <div className="preview">
          <img className="preview--img" src={articleData.images[0]}/>
          <h2 className="preview--title">{articleData.simplified_title}</h2>
        </div>
      )}
    </div>
  );
};

export default ArticlePreview;