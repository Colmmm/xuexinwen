import time, os, json, hashlib
import xml.etree.ElementTree as ET
import openai
from gnews import GNews
from newspaper import Article
from prompts import get_text_prompt, get_dict_prompt

class XueArticle(Article):

    def __init__(self, topic=None, url=None):
        if topic:
            self.topic = topic
            self.url = self._get_article_url_with_retry()
        elif url:
            self.url = url
        else:
            raise ValueError("Either a URL or a topic must be provided.")
            
        if self.url:
            # Generate a unique ID based on the URL using SHA-256 hash + with "a" prefix so doesn't start with number (also slicing it so not as long)
            self.article_id = "a" + hashlib.sha256(url.encode()).hexdigest()[:15]
            # Use url to download and parse article 
            super().__init__(self.url)
            self.download()
            self.parse()
        else:
            raise Exception("Failed to fetch the article URL after multiple attempts.")

    def _get_article_url_with_retry(self):
        attempts = 0
        MAX_RETRY_ATTEMPTS = 10
        while attempts < MAX_RETRY_ATTEMPTS:
            try:
                google_news = GNews(country='TW', language='zh-Hant', max_results=1)
                news_data = google_news.get_news(self.topic)
                return news_data[0]['url']
            except Exception as e:
                print(f"Error fetching article URL (attempt {attempts+1}): {str(e)}")
                attempts += 1
                time.sleep(1)  # Wait for 1 second before the next attempt

        return None

    def _call_openai_api(self, prompt):
        # Set up OpenAI API credentials
        api_key = os.environ.get('OPENAI_API_KEY')
        openai.api_key = api_key
        
        # Call OpenAI API
        response = openai.Completion.create(
            engine="gpt-3.5-turbo-instruct",  
            prompt=prompt,
            max_tokens=3000, 
            n=1  
        )
