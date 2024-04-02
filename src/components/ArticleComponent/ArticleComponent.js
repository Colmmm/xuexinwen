import React, { useEffect, useState } from 'react';
import './ArticleComponent.css';
import Navbar from '../Navbar/Navbar';
import config from '../../config';

const ArticleComponent = ({ articleId }) => {
    const [articleData, setArticleData] = useState(null);

    useEffect(() => {
        // Fetch the article data based on articleId
        fetch(`${config.apiUrl}/api/articles/${articleId}`)
            .then(response => response.json())
            .then(data => setArticleData(data))
            .catch(error => console.error('Error fetching article:', error));
    }, [articleId]);

    const renderDictionary = () => {
        if (articleData && articleData.keywords) {
            const keywordsObj = JSON.parse(articleData.keywords);

            return (
                <div className="dict">
                    <ul className="dict--list">
                        {Object.keys(keywordsObj).map(term => (
                            <li className="dict--item" key={term}>
                                <strong>{term}:</strong> {keywordsObj[term].description} ({keywordsObj[term].pinyin})
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
                        <h1 className="article--title">{articleData.simplified_title}</h1>
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