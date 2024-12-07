import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState, useEffect } from 'react'
import ArticleComponent from './components/ArticleComponent/ArticleComponent'
import Home from './components/Home/Home'
import './App.css'

function App() {
  const [articles, setArticles] = useState([])
  const apiUrl = import.meta.env.VITE_PRODUCTION === 'true' 
    ? 'http://xue-xinwen.com:5000' 
    : 'http://localhost:5000'

  useEffect(() => {
    fetch(`${apiUrl}/api/articles`)
      .then((response) => response.json())
      .then((data) => setArticles(data))
      .catch((error) => console.error('Error fetching articles:', error))
  }, [])

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home articles={articles} />} />
        <Route path="/article/:articleId/grade/:level" element={<ArticleComponent />} />
        <Route path="/article/:articleId" element={<ArticleComponent />} />
      </Routes>
    </Router>
  )
}

export default App
