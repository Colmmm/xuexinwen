import os
from typing import Dict
import requests

from article import Article
from logger_config import setup_logger
from db_manager import DatabaseManager

logger = setup_logger(__name__)

class ArticleProcessor:
    """Handles processing and grading of article content."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize processor with API key for language processing service.
        
        Args:
            api_key: API key for language processing service
        """
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
        logger.info(f"Initializing ArticleProcessor with API key: {'Present' if self.api_key else 'Missing'}")
        if not self.api_key:
            raise ValueError("API key is required for content processing")
        self.db = DatabaseManager()
    
    def process_article(self, article: Article, force: bool = False) -> Article:
        """
        Process an article, generating graded versions at beginner and intermediate levels.
        Handles duplicate checking and status updates.
        
        Args:
            article: Article to process
            force: Whether to force processing even if already processed
            
        Returns:
            Article: Processed article with graded versions added
        """
        logger.info(f"Processing article: {article.article_id}")
        
        # Check if article has already been processed
        exists, processed = self.db.check_article_status(article.article_id)
        
        if exists and processed and not force:
            logger.info(f"Article {article.article_id} already processed, skipping")
            return self.db.get_article(article.article_id)
        
        # Process the entire article content at once
        graded_versions = self._grade_content(article.mandarin_content, article.english_content)
        
        if graded_versions:
            logger.info("Received graded versions for article")
            # Split the graded content into sections
            for level, content in graded_versions.items():
                sections = content.split('\n\n')
                # Ensure we have the same number of sections as the original
                if len(sections) == len(article.sections):
                    for i, section_text in enumerate(sections):
                        article.sections[i].add_graded_version(level, section_text.strip())
                else:
                    logger.warning(f"Mismatch in number of sections for {level}")
        else:
            logger.warning("No graded versions received")
        
        # Store processed article and mark as processed
        self.db.add_article(article, processed=True)
        logger.info("Article processing complete")
        return article
    
    def _grade_content(self, mandarin_text: str, english_text: str) -> Dict[str, str]:
        """
        Create graded versions of the entire article content at beginner and intermediate levels.
        
        Args:
            mandarin_text: Complete Chinese text to grade
            english_text: Complete English translation for context
            
        Returns:
            Dict[str, str]: Dictionary mapping difficulty levels to graded text
        """
        try:
            logger.info("Making API call to grade content...")
            response = self._call_language_api({
                "task": "grade_all_levels",
                "mandarin_content": mandarin_text,
                "english_content": english_text
            })
            graded_versions = response.get('graded_versions', {})
            logger.info(f"Received {len(graded_versions)} graded versions")
            return graded_versions
        except Exception as e:
            logger.error(f"Error grading text: {str(e)}", exc_info=True)
            return {}
    
    def _call_language_api(self, data: Dict) -> Dict:
        """
        Make API call to language processing service.
        
        Args:
            data: Request data including task and content
            
        Returns:
            Dict: API response with graded versions
            
        Raises:
            requests.RequestException: If API call fails
        """
        logger.info("Preparing API call to OpenRouter...")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://xue-xinwen.com"
        }
        prompt = f"""
        Rewrite the following Chinese text at two difficulty levels (Beginner and Intermediate).
        Maintain the same paragraph structure as the original text.

        Important Instructions:

        Beginner Level:
        - Use only basic vocabulary and simple grammar patterns
        - Short, clear sentences with basic structures
        - Convert all proper nouns (names, places, organizations) to English
        - Focus on high-frequency words and essential grammar
        - Apart from keywords and names important for context, try to use only HSK 1-3 vocabulary

        Intermediate Level:
        - Use moderate vocabulary and grammar complexity
        - Mix of simple and compound sentences
        - Keep common Chinese names/places in Chinese, convert less common ones to English
        - Include some idiomatic expressions
        - Use vocabulary up to HSK 4-5 level

        Input:

        Original Chinese:
        {data['mandarin_content']}

        English Translation (Context):
        {data['english_content']}

        Output Format (strictly):
        BEGINNER:
        [Simplified Chinese text at beginner level, separated by original paragraph breaks]

        INTERMEDIATE:
        [Moderately complex Chinese text at intermediate level, separated by original paragraph breaks]
        """
        
        logger.info("Making request to OpenRouter API...")
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "openai/gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            
            logger.debug(f"API Response status code: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            logger.info("Successfully received JSON response")
            content = result['choices'][0]['message']['content'].strip()
            
            # Parse the response into a dictionary of graded versions
            graded_versions = {}
            current_level = None
            current_text = []
            
            logger.info("Parsing graded versions from response...")
            for line in content.split('\n'):
                line = line.strip()
                if line:
                    if line.startswith(('BEGINNER:', 'INTERMEDIATE:')):
                        # Save previous level if exists
                        if current_level and current_text:
                            graded_versions[current_level] = '\n\n'.join(current_text)
                            current_text = []
                        # Start new level
                        current_level = line.split(':')[0]
                        continue
                    current_text.append(line)
            
            # Save last level
            if current_level and current_text:
                graded_versions[current_level] = '\n\n'.join(current_text)
            
            logger.info(f"Successfully parsed {len(graded_versions)} graded versions")
            return {'graded_versions': graded_versions}
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}", exc_info=True)
            if hasattr(e.response, 'text'):
                logger.error(f"Error response: {e.response.text}")
            raise
