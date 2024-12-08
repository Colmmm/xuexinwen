import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../Navbar/Navbar'
import './ArticleComponent.css'

const GRADE_LEVELS = [
  { value: 'BEGINNER', label: '入门 (Beginner)' },
  { value: 'INTERMEDIATE', label: '中级 (Intermediate)' },
  { value: 'native', label: '高級/原文 (Advanced/Original)' }
]

const ArticleComponent = () => {
  const { articleId, level = 'native' } = useParams()
  const navigate = useNavigate()
  const [article, setArticle] = useState(null)
  const [error, setError] = useState(null)

  const apiUrl = import.meta.env.VITE_PRODUCTION === 'true'
    ? 'http://xue-xinwen.com:5000'
    : 'http://localhost:5000'

  useEffect(() => {
    setError(null)
    fetch(`${apiUrl}/api/articles/${articleId}/grade/${level}`)
      .then(response => {
        if (!response.ok) {
          throw new Error(`This article is not available in ${level === 'native' ? 'original' : level.toLowerCase()} level yet`)
        }
        return response.json()
      })
      .then(data => {
        setArticle(data)
        setError(null)
      })
      .catch(error => {
        console.error('Error fetching article:', error)
        setError(error.message)
      })
  }, [articleId, level, apiUrl])

  const handleGradeChange = (newLevel) => {
    navigate(`/article/${articleId}/grade/${newLevel}`)
  }

  if (error) {
    return (
      <div>
        <Navbar />
        <div className="article-container">
          <div className="article-error">
            <h2>Oops!</h2>
            <p>{error}</p>
            <button onClick={() => handleGradeChange('native')}>
              返回原文 (Return to Original Version)
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <Navbar />
      <div className="article-container">
        {article && (
          <div className="article">
            <div className="article--header">
              <h1 className="article--title-mandarin">{article.mandarin_title}</h1>
              <div className="article--meta">
                <span className="article--date">
                  {new Date(article.date).toLocaleDateString()}
                </span>
                <span className="article--source">
                  {article.source.toUpperCase()}
                </span>
                {article.authors && article.authors.length > 0 && (
                  <span className="article--authors">
                    By {article.authors.join(', ')}
                  </span>
                )}
              </div>
            </div>

            {article.image_url && (
              <div className="article--image-container">
                <img 
                  src={article.image_url} 
                  alt={article.mandarin_title}
                  className="article--image"
                />
              </div>
            )}

            <div className="article--grade-selector">
              {GRADE_LEVELS.map(({ value, label }) => (
                <button
                  key={value}
                  onClick={() => handleGradeChange(value)}
                  className={`grade-button ${level === value ? 'active' : ''}`}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="article--content">
              <div className="article--text-mandarin">
                {article.graded_content}
              </div>
            </div>

            <div className="article--footer">
              <a 
                href={article.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="article--source-link"
              >
                查看原文 (View Original Article)
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ArticleComponent
