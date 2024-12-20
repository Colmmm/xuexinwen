import './ArticlePreview.css'

const ArticlePreview = ({ article }) => {
  return (
    <div className="preview">
      {article.image_url && (
        <div className="preview--image-container">
          <img 
            src={article.image_url} 
            alt={article.mandarin_title}
            className="preview--image"
          />
        </div>
      )}
      <div className="preview--content">
        <div className="preview--titles">
          <h2 className="preview--title-mandarin">{article.mandarin_title}</h2>
          <h3 className="preview--title-english">{article.english_title}</h3>
        </div>
        <div className="preview--meta">
          <span className="preview--date">
            {new Date(article.date).toLocaleDateString()}
          </span>
          <span className="preview--source">{article.source.toUpperCase()}</span>
        </div>
      </div>
    </div>
  )
}

export default ArticlePreview
