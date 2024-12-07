from typing import List, Dict, Callable
import hashlib
from datetime import datetime

from article import Article, ArticleSection
from nyt_fetch_articles import nyt_fetch_articles

def generate_article_id(url: str) -> str:
    """Generate a unique article ID based on URL."""
    return "a" + hashlib.sha256(url.encode()).hexdigest()[:15]

def create_article_from_raw(raw_data: Dict, source: str) -> Article:
    """
    Create an Article instance from raw article data.
    
    Args:
        raw_data: Dictionary containing raw article data
        source: Identifier for the news source (e.g., 'nyt')
        
    Returns:
        Article: Created article instance
    """
    # Create ArticleSection instances from parallel texts
    sections = []
    for mand, eng in zip(raw_data['mandarin_paragraphs'], raw_data['english_paragraphs']):
        sections.append(ArticleSection(
            mandarin=mand,
            english=eng
        ))
    
    # Convert date string to datetime if needed
    if isinstance(raw_data['date'], str):
        date = datetime.fromisoformat(raw_data['date'].replace('Z', '+00:00'))
    else:
        date = raw_data['date']
    
    # Parse authors from string if needed
    if isinstance(raw_data['authors'], str):
        authors = [
            author.strip() 
            for author in raw_data['authors'].replace('and', ',').split(',')
            if author.strip() and author.strip() != 'No authors found'
        ]
    else:
        authors = raw_data['authors']
    
    # Create and return Article instance
    return Article(
        article_id=generate_article_id(raw_data['url']),
        url=raw_data['url'],
        date=date,
        source=source,
        authors=authors,
        mandarin_title=raw_data['chinese_title'],
        english_title=raw_data['english_title'],
        sections=sections
    )

# Dictionary mapping source IDs to their fetch functions
SOURCE_FETCHERS = {
    'nyt': nyt_fetch_articles
    # Add more sources here as needed, e.g.:
    # 'bbc': fetch_bbc_articles
}

def fetch_articles(source: str = None) -> List[Article]:
    """
    Fetch articles from specified source or all sources.
    
    Args:
        source: Optional source identifier. If None, fetch from all sources.
        
    Returns:
        List[Article]: List of fetched articles
        
    Raises:
        ValueError: If specified source is not supported
    """
    articles = []
    
    # Determine which sources to fetch from
    if source:
        if source not in SOURCE_FETCHERS:
            raise ValueError(f"Unsupported source: {source}")
        sources_to_fetch = {source: SOURCE_FETCHERS[source]}
    else:
        sources_to_fetch = SOURCE_FETCHERS
    
    # Fetch from each source
    for src_id, fetcher in sources_to_fetch.items():
        try:
            raw_articles = fetcher()
            for raw_article in raw_articles:
                article = create_article_from_raw(raw_article, src_id)
                articles.append(article)
        except Exception as e:
            print(f"Error fetching from {src_id}: {str(e)}")
    
    return articles

def register_source(source_id: str, fetcher: Callable[[], List[Dict]]) -> None:
    """
    Register a new source fetcher function.
    
    Args:
        source_id: Identifier for the news source
        fetcher: Function that fetches articles from this source
    """
    SOURCE_FETCHERS[source_id] = fetcher
