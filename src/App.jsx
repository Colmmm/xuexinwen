import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import ArticleComponent from './components/ArticleComponent/ArticleComponent'
import Home from './components/Home/Home'
import config from './config'
import './App.css'

function App() {
  const [articles, setArticles] = useState([])

  const fetchArticles = () => {
    fetch(`${config.apiUrl}/articles`)
      .then((response) => response.json())
      .then((data) => setArticles(data))
      .catch((error) => console.error('Error fetching articles:', error))
  }

  useEffect(() => {
    // Initial fetch
    fetchArticles()

    // Set up polling every 30 seconds
    const interval = setInterval(fetchArticles, 30000)

    // Cleanup interval on unmount
    return () => clearInterval(interval)
  }, [])

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home articles={articles} onRefresh={fetchArticles} />} />
        <Route path="/article/:articleId/grade/:level" element={<ArticleComponent />} />
        <Route path="/article/:articleId" element={<ArticleComponent />} />
      </Routes>
    </Router>
  )
}

export default App
