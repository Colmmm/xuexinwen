import React, { useEffect, useState } from 'react';
import './ArticleComponent.css';
import Navbar from '../Navbar/Navbar';

const ArticleComponent = ({ articleId }) => {
    const [articleData, setArticleData] = useState(null);

    useEffect(() => {
        // Fetch the article data based on articleId
        fetch(`http://localhost:5000/api/articles/${articleId}`)
            .then(response => response.json())
            .then(data => setArticleData(data))
            .catch(error => console.error('Error fetching article:', error));
    }, [articleId]);

    return (
        <div>        
            <Navbar />
            <div>
                {articleData && (
                    <>
                        <h1>{articleData.title}</h1>
                        <p>Simplified Text: {articleData.simplified_text}</p>
                        <div>
                            <h3>Dictionary:</h3>
                            <pre>{JSON.stringify(articleData.dict, null, 2)}</pre>
                        </div>
                    </>
                )}
                </div>
        </div>
    );
};

export default ArticleComponent;