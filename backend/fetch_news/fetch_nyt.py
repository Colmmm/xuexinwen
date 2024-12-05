import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional

# Define headers to be more respectful to the website
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def scrape_nyt_popular_article_urls(home_page_url: str = "https://cn.nytimes.com/") -> List[str]:
    """
    Scrapes popular article URLs from the NYT Chinese homepage.
    
    Args:
        home_page_url (str): The URL of the NYT Chinese homepage
        
    Returns:
        List[str]: A list of article URLs
        
    Raises:
        requests.RequestException: If there's an error fetching the homepage
    """
    try:
        # Get request on home page with headers
        response = requests.get(home_page_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        html_content = response.text
        
        # Parse html
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all article links within the "regularSummaryHeadline" class elements
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

        return article_links

    except requests.RequestException as e:
        print(f"Error fetching homepage: {str(e)}")
        return []

def scrape_nyt_article_contents(article_url: str) -> Optional[Dict]:
    """
    Scrapes the contents of a single NYT Chinese article.
    
    Args:
        article_url (str): The URL of the article to scrape
        
    Returns:
        Optional[Dict]: A dictionary containing the article contents, or None if scraping fails
        
    Raises:
        requests.RequestException: If there's an error fetching the article
    """
    try:
        # Get request article url with headers
        response = requests.get(article_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        html_content = response.text
            
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract Chinese and English titles
        chinese_title = ''
        english_title = ''
        
        try:
            chinese_title = soup.select('header h1:not([class])')[0].text.strip()
            english_title = soup.select('header h1.en-title')[0].text.strip()
        except IndexError:
            print(f"Error extracting titles from {article_url}")

        # Extract byline (author(s))
        byline = soup.find('div', class_='byline')
        authors = byline.find('address').text.strip() if byline and byline.find('address') else 'No authors found'

        # Extract publication date
        date_elem = soup.find('time', {'datetime': True})
        date = date_elem['datetime'] if date_elem else 'No date found'

        # Extract the Chinese and English paragraphs in pairs
        english_paragraphs = []
        mandarin_paragraphs = []

        # Find all dual-body items that contain the Mandarin and English text
        dual_body_items = soup.find_all('div', class_='row article-dual-body-item')

        try:
            # Loop through the dual-body items and extract English and Mandarin paragraphs
            for item in dual_body_items:
                cols = item.find_all('div', class_='col-lg-6')
                
                if len(cols) == 2:
                    # Extract English paragraph (first column)
                    english = cols[0].find('div', class_='article-paragraph')
                    if english:
                        english_paragraphs.append(english.text.strip())

                    # Extract Mandarin paragraph (second column)
                    mandarin = cols[1].find('div', class_='article-paragraph')
                    if mandarin:
                        mandarin_paragraphs.append(mandarin.text.strip())
        except Exception as e:
            print(f"Error extracting dual body paragraphs from {article_url}: {str(e)}")

        return {
            'chinese_title': chinese_title,
            'english_title': english_title,
            'authors': authors,
            'date': date,
            'english_paragraphs': english_paragraphs,
            'mandarin_paragraphs': mandarin_paragraphs,
            'url': article_url
        }

    except requests.RequestException as e:
        print(f"Error fetching article {article_url}: {str(e)}")
        return None
    except Exception as e:
        print(f"Error processing article {article_url}: {str(e)}")
        return None

def fetch_nyt_articles() -> List[Dict]:
    """
    Main function to fetch and process NYT Chinese articles.
    
    Returns:
        List[Dict]: A list of dictionaries containing article contents
    """
    # Get popular article URLs
    article_urls = scrape_nyt_popular_article_urls()
    articles = []

    # Process content of popular articles with delay
    for url in article_urls:
        article_content = scrape_nyt_article_contents(url)
        if article_content:
            articles.append(article_content)
        
        # Add 12-second delay between requests
        time.sleep(12)

    return articles

if __name__ == "__main__":
    articles = fetch_nyt_articles()
    print(f"Successfully scraped {len(articles)} articles")
