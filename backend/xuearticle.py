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
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use the appropriate model
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        # XML-like data outputed
        raw_xml = response['choices'][0]['message']['content']

        # Parse the XML
        parsed_xml = ET.fromstring(raw_xml) 
        return parsed_xml


    def simplify_text(self):
        # get prompt for openai api to simplify text
        prompt = get_text_prompt(self)

        # call api, output will be xml data
        simplified_article = self._call_openai_api(prompt) 

        # extract title and text from xml data
        self.simplified_title = simplified_article.find("title").text
        self.simplified_text = simplified_article.find("text").text



    def generate_dict(self):
        # get prompt for openai api to simplify text
        prompt = get_dict_prompt(self)

        # call api, output will be xml data
        article_dict = self._call_openai_api(prompt).find("dictionary")

        # create dict attribute
        self.dict = {}

        # Process each entry and add to dict
        for entry in article_dict.findall('entry'):
            word = entry.find('word').text
            pinyin = entry.find('pinyin').text
            description = entry.find('description').text
            # assign values
            self.dict[word] = {'pinyin': pinyin, 'description': description}

    def to_json(self):

        # Extract desired attributes
        data = {
            "id": self.article_id,
            "title": self.title,
            "text": self.text,
            "url": self.url,
            "images": list(self.images)
        }

        # Add optional attributes if they exist
        if self.simplified_title:
            data["simplified_title"] = self.simplified_title

        if self.simplified_text:
            data["simplified_text"] = self.simplified_text
        
        if self.dict:
            data["dict"] = self.dict
        
        # Convert to JSON and return
        return json.dumps(data, indent=4)

    def save_to_json(self, dir):

        # Create the directory if it doesn't exist
        if not os.path.exists(dir):
            os.makedirs(dir)

        # Create JSON representation
        json_data = self.to_json()

        # Write to file using article ID as name
        filepath = os.path.join(dir, f"{self.article_id}.json")
        with open(filepath, "w") as json_file:
            json_file.write(json_data)
