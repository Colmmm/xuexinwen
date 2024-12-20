from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import os

from ..article.article import Article
from ..article.article_processor import ArticleProcessor
from ..fetching.fetch_articles import fetch_articles
from ..database.db_manager import DatabaseManager
from ..utils.logger_config import setup_logger

logger = setup_logger(__name__)

app = FastAPI(title="News Article API")

# Define allowed origins based on the environment
BACKEND_PRODUCTION = os.getenv("BACKEND_PRODUCTION", "false").lower() == "true"
if BACKEND_PRODUCTION:
    origins = [
        "https://xue-xinwen.com",  # Production domain
        "https://www.xue-xinwen.com"  # Optional subdomain
    ]
else:
    origins = [
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",  # Localhost with explicit IP
    ]

logger.info(f"Configuring CORS with origins: {origins}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = DatabaseManager()
processor = ArticleProcessor(tocfl_csv_path="backend/assets/official_tocfl_list_processed.csv")

# Enums for validation
class GradeLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    NATIVE = "native"

# Pydantic models for API responses
class ArticleResponse(BaseModel):
    article_id: str
    url: str
    date: datetime
    source: str
    authors: List[str]
    mandarin_title: str
    english_title: str
    mandarin_content: str
    english_content: str
    section_indices: List[tuple]
    image_url: Optional[str] = None
    graded_content: Optional[Dict[str, str]] = None
    metadata: Optional[Dict] = None
    
    class Config:
        from_attributes = True

class ProcessedArticleResponse(BaseModel):
    article_id: str
    url: str
    date: datetime
    source: str
    authors: List[str]
    mandarin_title: str
    english_title: str
    html_versions: Dict[str, str]  # Level -> HTML content mapping
    entities: Dict[str, Dict[str, str]]  # Entity type -> {word: definition}
    word_levels: Dict[str, List[str]]  # CEFR level -> word list
    image_url: Optional[str] = None
    metadata: Optional[Dict] = None

@app.get("/api/articles", response_model=List[ArticleResponse])
async def get_articles(
    source: Optional[str] = None,
    limit: int = Query(default=10, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get a list of articles with optional filtering."""
    try:
        logger.info(f"Fetching articles - source: {source}, limit: {limit}, offset: {offset}")
        articles = db.get_articles(
            source=source,
            limit=limit,
            offset=offset
        )
        logger.info(f"Successfully retrieved {len(articles)} articles")
        return articles
    except Exception as e:
        logger.error(f"Error retrieving articles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving articles: {str(e)}"
        )

@app.get("/api/articles/{article_id}", response_model=ProcessedArticleResponse)
async def get_article(article_id: str):
    """Get processed article content with HTML wrapping and analysis."""
    logger.info(f"Fetching article: {article_id}")
    
    # Get the article
    article = db.get_article(article_id)
    if not article:
        logger.warning(f"Article not found: {article_id}")
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    
    # Process the article if not already processed
    try:
        processed = processor.process_article(article)
        logger.info(f"Successfully processed article: {article_id}")
        
        return {
            "article_id": article.article_id,
            "url": article.url,
            "date": article.date,
            "source": article.source,
            "authors": article.authors,
            "mandarin_title": article.mandarin_title,
            "english_title": article.english_title,
            "html_versions": processed['html_versions'],
            "entities": processed['entities'],
            "word_levels": processed['word_levels'],
            "image_url": article.image_url,
            "metadata": article.metadata
        }
    except Exception as e:
        logger.error(f"Error processing article {article_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing article: {str(e)}"
        )

@app.get("/api/articles/{article_id}/grade/{level}", response_model=ProcessedArticleResponse)
async def get_graded_article(
    article_id: str,
    level: GradeLevel
):
    """
    Get a specific version of an article (graded or native).
    
    Args:
        article_id: The ID of the article
        level: The grade level (BEGINNER, INTERMEDIATE, or native)
    """
    logger.info(f"Fetching graded article: {article_id}, level: {level}")
    
    # Get and process the article
    article = db.get_article(article_id)
    if not article:
        logger.warning(f"Article not found: {article_id}")
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    
    try:
        processed = processor.process_article(article)
        
        # Check if the requested level exists
        if level.value not in processed['html_versions']:
            logger.warning(f"Level {level.value} not available for article: {article_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Level {level.value} not available for this article"
            )
        
        logger.info(f"Successfully retrieved {level.value} version of article: {article_id}")
        return {
            "article_id": article.article_id,
            "url": article.url,
            "date": article.date,
            "source": article.source,
            "authors": article.authors,
            "mandarin_title": article.mandarin_title,
            "english_title": article.english_title,
            "html_versions": processed['html_versions'],
            "entities": processed['entities'],
            "word_levels": processed['word_levels'],
            "image_url": article.image_url,
            "metadata": article.metadata
        }
    except Exception as e:
        logger.error(f"Error processing article {article_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing article: {str(e)}"
        )

@app.post("/api/articles/fetch")
async def fetch_new_articles(
    background_tasks: BackgroundTasks,
    source: Optional[str] = None
):
    """
    Fetch and process new articles from specified source or all sources.
    Processing happens in the background.
    """
    try:
        logger.info(f"Starting fetch of new articles from source: {source if source else 'all'}")
        # Fetch articles
        raw_articles = fetch_articles(source)
        
        if not raw_articles:
            logger.info("No new articles found to process")
            return {
                "message": "No new articles found to process"
            }
        
        # Queue all articles for processing
        for article in raw_articles:
            logger.info(f"Queueing article for processing: {article.article_id}")
            background_tasks.add_task(processor.process_article, article)
            background_tasks.add_task(db.save_article, article)
        
        logger.info(f"Started processing {len(raw_articles)} articles")
        return {
            "message": f"Started processing {len(raw_articles)} articles"
        }
    except Exception as e:
        logger.error(f"Error fetching articles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching articles: {str(e)}"
        )

@app.post("/api/articles/{article_id}/reprocess")
async def reprocess_article(
    article_id: str,
    background_tasks: BackgroundTasks
):
    """
    Reprocess an existing article to generate new analysis and graded versions.
    Processing happens in the background.
    """
    logger.info(f"Requesting reprocess of article: {article_id}")
    
    # Get the article
    article = db.get_article(article_id)
    if not article:
        logger.warning(f"Article not found for reprocessing: {article_id}")
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    
    try:
        # Process immediately to catch any errors
        processed = processor.process_article(article)
        
        # Save the processed article
        background_tasks.add_task(db.save_article, article)
        
        logger.info(f"Successfully reprocessed article: {article_id}")
        return {
            "message": f"Successfully reprocessed article {article_id}",
            "html_versions": processed['html_versions'],
            "entities": processed['entities'],
            "word_levels": processed['word_levels']
        }
    except Exception as e:
        logger.error(f"Error reprocessing article {article_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error reprocessing article: {str(e)}"
        )
