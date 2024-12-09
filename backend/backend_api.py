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
        articles = db.get_articles(
            source=source,
            limit=limit,
            offset=offset
        )
        return articles
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving articles: {str(e)}"
        )

@app.get("/api/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str):
    """Get metadata and content for a specific article."""
    article = db.get_article(article_id)
    if not article:
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
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
    article = db.get_article(article_id)
    if not article:
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    
    if level == GradeLevel.NATIVE:
        # Return native (original) version
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
            raise HTTPException(
                status_code=404,
                detail=f"Graded version not available for {level.value.lower()} level"
            )
        
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
        # Fetch articles
        raw_articles = fetch_articles(source)
        
        if not raw_articles:
            return {
                "message": "No new articles found to process"
            }
        
        # Filter out already processed articles
        new_articles = []
        for article in raw_articles:
            exists, processed = db.check_article_status(article.article_id)
            
            if not exists:
                # Add to database unprocessed
                db.add_article(article, processed=False)
                new_articles.append(article)
            elif not processed:
                # Get existing unprocessed article
                stored_article = db.get_article(article.article_id)
                if stored_article:
                    new_articles.append(stored_article)
        
        if not new_articles:
            return {
                "message": "No new articles to process"
            }
        
        # Queue background processing for new/unprocessed articles
        for article in new_articles:
            background_tasks.add_task(process_and_store_article, article)
        
        return {
            "message": f"Started processing {len(new_articles)} articles"
        }
    except Exception as e:
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
    exists, processed = db.check_article_status(article_id)
    if not exists:
        raise HTTPException(
            status_code=404,
            detail="Article not found"
        )
    
    article = db.get_article(article_id)
    background_tasks.add_task(process_and_store_article, article)
    
    return {
        "message": f"Started reprocessing article {article_id}"
    }

def process_and_store_article(article: Article):
    """Background task to process and store an article."""
    try:
        # Generate graded versions
        processed_article = processor.process_article(article)
        # Store in database and mark as processed
        db.add_article(processed_article, processed=True)
    except Exception as e:
        print(f"Error processing article {article.article_id}: {str(e)}")

# Initial fetch of articles if database is empty
@app.on_event("startup")
async def startup_event():
    try:
        articles = db.get_articles(limit=1)
        if not articles:
            print("Database empty, performing initial fetch...")
            await fetch_new_articles(None)
    except Exception as e:
        print(f"Error during startup fetch: {str(e)}")
