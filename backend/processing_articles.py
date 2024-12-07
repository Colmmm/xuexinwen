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
        print(f"Initializing ArticleProcessor with API key: {'Present' if self.api_key else 'Missing'}")
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
        print(f"\nProcessing article: {article.english_title}")
        print(f"Number of sections to process: {len(article.sections)}")
        
        # Process each section
        for i, section in enumerate(article.sections, 1):
            print(f"\nProcessing section {i}/{len(article.sections)}")
            print(f"Original mandarin text: {section.mandarin[:100]}...")
            print(f"Original english text: {section.english[:100]}...")
            
            # Get all graded versions in one API call
            graded_versions = self._grade_section(section.mandarin, section.english)
            if graded_versions:
                print(f"Received graded versions for section {i}")
                # Add each graded version to the section
                for level, text in graded_versions.items():
                    print(f"Adding {level} version: {text[:50]}...")
                    section.add_graded_version(level, text)
            else:
                print(f"No graded versions received for section {i}")
            break # lets only focus on one section for now
        
        print("\nArticle processing complete")
        return article
    
    def _grade_section(self, mandarin_text: str, english_text: str) -> Dict[str, str]:
        """
        Create graded versions of text at all CEFR levels.
        
        Args:
            mandarin_text: Chinese text to grade
            english_text: English translation for context
            
        Returns:
            Dict[str, str]: Dictionary mapping CEFR levels to graded text
        """
        try:
            print("\nMaking API call to grade section...")
            response = self._call_language_api({
                "task": "grade_all_levels",
                "mandarin_content": mandarin_text,
                "english_content": english_text
            })
            graded_versions = response.get('graded_versions', {})
            print(f"Received {len(graded_versions)} graded versions")
            return graded_versions
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
        print("\nPreparing API call to OpenRouter...")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://xue-xinwen.com"
        }
        prompt=f"""
        Rewrite the following Chinese text at four CEFR levels (A1, A2, B1, B2).

        Important Instructions:

            Proper Nouns (Names, Places, Organizations):
                A1: Convert all proper nouns (e.g., names of people, places, organizations) into English, even if they're common or obvious.
                A2: Convert most proper nouns into English except universally recognized ones like 中國 (China) or 美國 (USA).
                B1: Use a mix of English and Chinese for names—retain common Chinese names in their original form and use English for less familiar ones.
                B2: Retain proper nouns in Chinese unless English is more natural in context.
            Vocabulary and Grammar:
                A1: Use the simplest vocabulary and grammar. Short, clear sentences are preferred.
                A2: Slightly more complex than A1, maintaining clear structure.
                B1: Use moderately complex vocabulary and grammar suitable for intermediate learners.
                B2: Use vocabulary and grammar closest to the original text.
            Meaning: Keep the main meaning of the text consistent across all levels.
            Output Only the Text: Do not include any explanations, comments, or deviations from the format below.

        Input:

            Original Chinese:
            {data['mandarin_content']}
            English Translation (Context):
            {data['english_content']}

        Output Format (strictly):
        A1: [Simplified Mandarin text at A1 level with all names in English]  
        A2: [Simplified Mandarin text at A2 level with most names in English, except obvious ones like 中國/China]  
        B1: [Simplified Mandarin text at B1 level with a mix of English and Chinese names]  
        B2: [Simplified Mandarin text at B2 level, closest to original complexity, using Chinese for most names]  
        Additional Emphasis:
        Names (e.g., "John", "Microsoft", "Beijing") and proper nouns must be converted to English at the A1 and A2 levels unless they are very obvious or universally recognized. 
        Double-check the output to ensure names are correctly handled.
        """ 
        
        print("Making request to OpenRouter API...")
        # Make API call
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    #"model": "meta-llama/llama-3.1-70b-instruct:free",  # Using free model while testing instead of "openai/gpt-4-mini",
                    "model": "openai/gpt-4-mini",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            
            print(f"API Response status code: {response.status_code}")
            response.raise_for_status()
            
            # Parse response to extract graded versions
            result = response.json()
            print("Successfully received JSON response")
            content = result['choices'][0]['message']['content'].strip()
            
            # Parse the response into a dictionary of graded versions
            graded_versions = {}
            current_level = None
            current_text = []
            
            print("\nParsing graded versions from response...")
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
            
            print(f"Successfully parsed {len(graded_versions)} graded versions")
            return {'graded_versions': graded_versions}
            
        except requests.RequestException as e:
            print(f"API request failed: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Error response: {e.response.text}")
            raise
