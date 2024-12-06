import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import schedule
import time
from threading import Thread
import os

from fetch_articles import fetch_articles
from processing_articles import ArticleProcessor
from db_manager import DatabaseManager
from backend_api import app as api_app

# Initialize components
db = DatabaseManager()
processor = ArticleProcessor()

def fetch_and_process_articles():
    """Fetch and process articles from all sources."""
    try:
        # Fetch articles
        articles = fetch_articles()
        
        # Process and store each article
        for article in articles:
            try:
                processed_article = processor.process_article(article)
                db.add_article(processed_article)
            except Exception as e:
                print(f"Error processing article {article.article_id}: {str(e)}")
            
        print(f"Successfully processed {len(articles)} articles")
    except Exception as e:
        print(f"Error in fetch and process routine: {str(e)}")

def run_scheduler():
    """Run the scheduler in a separate thread."""
    # Schedule article fetching every 6 hours
    schedule.every(6).hours.do(fetch_and_process_articles)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application."""
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Start the scheduler in a separate thread
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Do an initial fetch of articles if database is empty
    try:
        articles = db.get_articles(limit=1)
        if not articles:
            print("Database empty, performing initial fetch...")
            fetch_and_process_articles()
    except Exception as e:
        print(f"Error during initial fetch: {str(e)}")
    
    yield
    
    # Cleanup could be added here if needed
    pass

# Add lifespan handler to the API app
api_app.router.lifespan = lifespan

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the FastAPI application
    uvicorn.run(
        "main:api_app",
        host="0.0.0.0",
        port=port,
        reload=not os.environ.get('BACKEND_PRODUCTION', 'false').lower() == 'true'
    )
