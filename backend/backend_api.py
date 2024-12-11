from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
import os

from article import Article
from fetch_articles import fetch_articles, generate_article_id
from processing_articles import ArticleProcessor
from db_manager import DatabaseManager
from logger_config import setup_logger

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

db = DatabaseManager()
processor = ArticleProcessor()

# Enums for validation
class GradeLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    NATIVE = "native"

# Pydantic models for API responses
class ArticleSection(BaseModel):
    mandarin: str
    english: str
    graded: Optional[Dict[str, str]] = None
    
    class Config:
        from_attributes = True

class ArticleResponse(BaseModel):
    article_id: str
    url: str
    date: datetime
    source: str
    authors: List[str]
    mandarin_title: str
    english_title: str
    sections: List[ArticleSection]
    image_url: Optional[str] = None
    metadata: Optional[Dict] = None
    
    class Config:
        from_attributes = True

class GradedArticleResponse(BaseModel):
    article_id: str
    url: str
    date: datetime
    source: str
    authors: List[str]
    mandarin_title: str
    english_title: str
    graded_content: str
    english_content: str
    image_url: Optional[str] = None
    metadata: Optional[Dict] = None

@app.get("/api/articles", response_model=List[ArticleResponse])
@app.get("/api/articles/", response_model=List[ArticleResponse])
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

@app.get("/api/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str):
    """Get metadata and content for a specific article."""
    logger.info(f"Fetching article: {article_id}")
    article = db.get_article(article_id)
    if not article:
        logger.warning(f"Article not found: {article_id}")
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    logger.info(f"Successfully retrieved article: {article_id}")
    return article

@app.get("/api/articles/{article_id}/grade/{level}", response_model=GradedArticleResponse)
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
    article = db.get_article(article_id)
    if not article:
        logger.warning(f"Article not found: {article_id}")
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    
    if level == GradeLevel.NATIVE:
        # Return native (original) version
        logger.info(f"Returning native version of article: {article_id}")
        return {
            "article_id": article.article_id,
            "url": article.url,
            "date": article.date,
            "source": article.source,
            "authors": article.authors,
            "mandarin_title": article.mandarin_title,
            "english_title": article.english_title,
            "graded_content": "\n\n".join(s.mandarin for s in article.sections),
            "english_content": "\n\n".join(s.english for s in article.sections),
            "image_url": article.image_url,
            "metadata": article.metadata
        }
    else:
        # Check if any sections have the requested level
        graded_sections = [
            s.graded[level.value] if s.graded and level.value in s.graded else s.mandarin
            for s in article.sections
        ]
        
        if not any(s.graded and level.value in s.graded for s in article.sections):
            logger.warning(f"Graded version not available for {level.value} level in article: {article_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Graded version not available for {level.value.lower()} level"
            )
        
        logger.info(f"Returning {level.value} version of article: {article_id}")
        return {
            "article_id": article.article_id,
            "url": article.url,
            "date": article.date,
            "source": article.source,
            "authors": article.authors,
            "mandarin_title": article.mandarin_title,
            "english_title": article.english_title,
            "graded_content": "\n\n".join(graded_sections),
            "english_content": "\n\n".join(s.english for s in article.sections),
            "image_url": article.image_url,
            "metadata": article.metadata
        }

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
        # process_article now handles all database operations internally
        for article in raw_articles:
            logger.info(f"Queueing article for processing: {article.article_id}")
            background_tasks.add_task(processor.process_article, article)
        
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
    Reprocess an existing article to generate new graded versions.
    Processing happens in the background.
    """
    logger.info(f"Requesting reprocess of article: {article_id}")
    
    # Get the article - if it doesn't exist, this will return None
    article = db.get_article(article_id)
    if not article:
        logger.warning(f"Article not found for reprocessing: {article_id}")
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    
    logger.info(f"Queueing article for reprocessing: {article_id}")
    # Force reprocessing even if already processed
    background_tasks.add_task(processor.process_article, article, force=True)
    
    return {
        "message": f"Started reprocessing article {article_id}"
    }
