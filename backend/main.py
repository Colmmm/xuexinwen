import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

from fetch_articles import fetch_articles
from processing_articles import ArticleProcessor
from db_manager import DatabaseManager
from backend_api import app as api_app

from logger_config import setup_logger
logger = setup_logger(__name__)


# Initialize components
db = DatabaseManager()
processor = ArticleProcessor()

async def fetch_and_process_articles():
    """Fetch and process articles from all sources."""
    try:
        logger.info("Starting article fetch and process routine")
        # Fetch articles (non-async)
        articles = fetch_articles()
        
        if not articles:
            logger.info("No new articles found")
            return
        
        # Process each article
        processed_count = 0
        for article in articles:
            try:
                # process_article now handles all database operations internally
                processor.process_article(article)
                processed_count += 1
            except Exception as e:
                logger.error(f"Error processing article {getattr(article, 'article_id', 'unknown')}: {str(e)}", exc_info=True)
            
        logger.info(f"Successfully processed {processed_count} out of {len(articles)} articles")
        
    except Exception as e:
        logger.error(f"Error in fetch and process routine: {str(e)}", exc_info=True)

async def scheduler():
    """Async scheduler for periodic article fetching."""
    logger.info("Article fetch scheduler started")
    while True:
        try:
            await fetch_and_process_articles()
            next_run = datetime.now() + timedelta(hours=6)
            logger.info(f"Next scheduled run at: {next_run}")
            await asyncio.sleep(6 * 60 * 60) # wait 6 hours till next schedule
            #await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}", exc_info=True)
            await asyncio.sleep(60)

async def initial_fetch():
    """Perform initial fetch of articles if database is empty."""
    try:
        articles = db.get_articles(limit=1)  # non-async
        if not articles:
            logger.info("Database empty, performing initial fetch...")
            await fetch_and_process_articles()
        else:
            logger.info("Database already contains articles, skipping initial fetch")
    except Exception as e:
        logger.error(f"Error checking database for initial fetch: {str(e)}", exc_info=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting application...")
    
    # Start the scheduler as a background task
    scheduler_task = asyncio.create_task(scheduler())
    
    # Perform initial fetch
    await initial_fetch()
    
    yield
    
    # Cleanup
    logger.info("Shutting down application...")
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        logger.info("Scheduler task cancelled")

# Create FastAPI app instance
app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_app.router)

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the FastAPI application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=not os.environ.get('BACKEND_PRODUCTION', 'false').lower() == 'true'
    )
