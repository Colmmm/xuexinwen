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

    const renderDictionary = () => {
        if (articleData && articleData.dict) {
            return (
                <div className="dict">
                    <ul className="dict--list">
                        {Object.keys(articleData.dict).map(term => (
                            <li className="dict--item" key={term}>
                                <strong>{term}:</strong> {articleData.dict[term].description} ({articleData.dict[term].pinyin})
                            </li>
                        ))}
                    </ul>
                </div>
            );
        }
    };

    return (
        <div className="article-container">
            <Navbar />
            <div className="article">
                {articleData && (
                    <>
                        <h1 className="article--title">{articleData.title}</h1>
                        <img className="article--img" src={articleData.images[0]}/>
                        {renderDictionary()}
                        <p className="article--text">{articleData.simplified_text}</p>
                    </>
                )}
            </div>
        </div>
    );
};

export default ArticleComponent;