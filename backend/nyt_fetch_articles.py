import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
from datetime import datetime

# Define headers to be more respectful to the website
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def scrape_article_urls(home_page_url: str = "https://cn.nytimes.com/") -> List[str]:
    """
    Scrapes article URLs from the NYT Chinese homepage.
    
    Args:
        home_page_url: The URL of the NYT Chinese homepage
        
    Returns:
        List of article URLs
    """
    try:
        print(f"\nFetching homepage: {home_page_url}")
        response = requests.get(home_page_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        article_links = []
        for article in soup.select('.regularSummaryHeadline a'):
            link = article.get('href')
            if link:
                # Ensure the URL ends with /dual/
                if not link.endswith('/'):
                    link = f"{link}/"
                if not link.endswith('dual/'):
                    link = f"{link}dual/"
                full_url = f"https://cn.nytimes.com{link}"
                article_links.append(full_url)
                print(f"Found article URL: {full_url}")

        print(f"Total articles found: {len(article_links)}")
        return article_links

    except requests.RequestException as e:
        print(f"Error fetching homepage: {str(e)}")
        return []

def scrape_article_content(article_url: str) -> Optional[Dict]:
    """
    Scrapes the content of a single NYT Chinese article.
    
    Args:
        article_url: The URL of the article to scrape
        
    Returns:
        Dictionary containing article content or None if scraping fails
    """
    try:
        print(f"\nScraping article: {article_url}")
        response = requests.get(article_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract titles
        try:
            mandarin_title = soup.select('header h1:not([class])')[0].text.strip()
            english_title = soup.select('header h1.en-title')[0].text.strip()
            print(f"Found titles - Mandarin: {mandarin_title[:30]}... English: {english_title[:30]}...")
        except IndexError as e:
            print(f"Error extracting titles from {article_url}: {str(e)}")
            print("Header content:", soup.select('header'))
            return None

        # Extract byline
        byline = soup.find('div', class_='byline')
        authors = byline.find('address').text.strip() if byline and byline.find('address') else 'No authors found'
        print(f"Authors: {authors}")

        # Extract date
        date_elem = soup.find('time', {'datetime': True})
        date = date_elem['datetime'] if date_elem else datetime.now().isoformat()
        print(f"Date: {date}")

        # Extract parallel paragraphs
        english_paragraphs = []
        mandarin_paragraphs = []

        for item in soup.find_all('div', class_='row article-dual-body-item'):
            cols = item.find_all('div', class_='col-lg-6')
            if len(cols) == 2:
                eng = cols[0].find('div', class_='article-paragraph')
                mand = cols[1].find('div', class_='article-paragraph')
                
                if eng and mand:
                    english_paragraphs.append(eng.text.strip())
                    mandarin_paragraphs.append(mand.text.strip())

        print(f"Extracted {len(english_paragraphs)} paragraph pairs")

        # Only return if we have both titles and at least one paragraph pair
        if mandarin_title and english_title and english_paragraphs and mandarin_paragraphs:
            article_data = {
                'url': article_url,
                'mandarin_title': mandarin_title,
                'english_title': english_title,
                'authors': authors,
                'date': date,
                'english_paragraphs': english_paragraphs,
                'mandarin_paragraphs': mandarin_paragraphs
            }
            print("Successfully created article data dictionary")
            return article_data
        
        print("Missing required data, skipping article")
        return None

    except Exception as e:
        print(f"Error scraping article {article_url}: {str(e)}")
        return None

def nyt_fetch_articles() -> List[Dict]:
    """
    Fetch and process NYT Chinese articles.
    
    Returns:
        List of dictionaries containing article contents
    """
    print("\nStarting NYT article fetch process...")
    article_urls = scrape_article_urls()
    articles = []

    for url in article_urls: 
        article_content = scrape_article_content(url)
        if article_content:
            articles.append(article_content)
            print(f"Successfully added article to collection. Total articles: {len(articles)}")
            break # lets process only one article for testing purposes
        else:
            print(f"Skipping article {url} due to missing content")
        time.sleep(12)  # Respectful delay between requests

    print(f"\nFetch process complete. Total articles collected: {len(articles)}")
    return articles
