import os
from typing import Dict
import requests

from article import Article

class ArticleProcessor:
    """Handles processing and grading of article content."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize processor with API key for language processing service.
        
        Args:
            api_key: API key for language processing service
        """
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("API key is required for content processing")
    
    def process_article(self, article: Article) -> Article:
        """
        Process an article, generating graded versions for each section.
        
        Args:
            article: Article to process
            
        Returns:
            Article: Processed article with graded versions added
        """
        # Process each section
        for section in article.sections:
            # Get all graded versions in one API call
            graded_versions = self._grade_section(section.mandarin)
            if graded_versions:
                # Add each graded version to the section
                for level, text in graded_versions.items():
                    section.add_graded_version(level, text)
        
        return article
    
    def _grade_section(self, text: str) -> Dict[str, str]:
        """
        Create graded versions of text at all CEFR levels.
        
        Args:
            text: Text to grade
            
        Returns:
            Dict[str, str]: Dictionary mapping CEFR levels to graded text
        """
        try:
            response = self._call_language_api({
                "task": "grade_all_levels",
                "content": text
            })
            return response.get('graded_versions', {})
        except Exception as e:
            print(f"Error grading text: {str(e)}")
            return {}
    
    def _call_language_api(self, data: Dict) -> Dict:
        """
        Make API call to language processing service.
        
        Args:
            data: Request data including task and content
            
        Returns:
            Dict: API response with graded versions for all CEFR levels
            
        Raises:
            requests.RequestException: If API call fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://xue-xinwen.com"
        }
        
        prompt = f"""
        Please rewrite the following Chinese text at four different CEFR levels (A1, A2, B1, B2).
        For each level, maintain the main meaning while using vocabulary and grammar
        appropriate for that level of Chinese learners.

        Original text:
        {data['content']}

        Respond in this exact format:
        A1: [A1 level text here]
        A2: [A2 level text here]
        B1: [B1 level text here]
        B2: [B2 level text here]

        Only include the level markers and the graded text, no other explanations.
        """
        
        # Make API call
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "openai/gpt-4-mini",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )
        
        response.raise_for_status()
        
        # Parse response to extract graded versions
        result = response.json()
        content = result['choices'][0]['message']['content'].strip()
        
        # Parse the response into a dictionary of graded versions
        graded_versions = {}
        current_level = None
        current_text = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line:
                if line.startswith(('A1:', 'A2:', 'B1:', 'B2:')):
                    # Save previous level if exists
                    if current_level and current_text:
                        graded_versions[current_level] = ' '.join(current_text)
                        current_text = []
                    # Start new level
                    current_level = line[:2]
                    current_text = [line[3:].strip()]
                else:
                    # Continue current level
                    current_text.append(line)
        
        # Save last level
        if current_level and current_text:
            graded_versions[current_level] = ' '.join(current_text)
        
        return {'graded_versions': graded_versions}
