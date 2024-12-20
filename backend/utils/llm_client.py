import os
import json
import requests
from typing import Dict, Optional, List
from ..prompts.entity_extraction_prompt import get_entity_extraction_prompt
from ..prompts.tocfl_tagger_prompt import get_word_classification_prompt
from ..prompts.simplification_prompt import get_simplification_prompt, get_multi_level_prompt

class LLMClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")

    def _make_request(self, prompt, model="openai/gpt-4o-mini", temperature=0.1):
        """Make a request to the OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://xuexinwen.com",
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API request failed: {e}")
            return None

    def _clean_json_response(self, content):
        """Clean and parse JSON response from the API."""
        if not content:
            return None
            
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        if content.rstrip().endswith(','):
            content = content.rstrip().rstrip(',') + ']'
            
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            if content.count('[') > content.count(']'):
                content = content + ']'
            try:
                return json.loads(content)
            except:
                print(f"Failed to parse JSON even after cleanup: {content}")
                return None

    def extract_entities(self, zh_content, en_content):
        """Extract entities from parallel Chinese and English texts."""
        prompt = get_entity_extraction_prompt(zh_content, en_content)
        
        response = self._make_request(prompt)
        return self._clean_json_response(response)

    def classify_words(self, words):
        """Classify Chinese words into CEFR levels."""
        if not words:
            return {}
            
        words_str = ", ".join(words)
        prompt = get_word_classification_prompt(words_str)
        
        response = self._make_request(prompt)
        return self._clean_json_response(response)

    def simplify_article(self, zh_content: str, en_content: str, target_level: str = 'B1') -> str:
        """
        Simplify a Chinese article to a target CEFR level.
        
        Args:
            zh_content: Original Chinese content
            en_content: Original English content (for context)
            target_level: Target CEFR level for simplification
            
        Returns:
            Simplified Chinese text, or None if simplification fails
        """
        prompt = get_simplification_prompt(zh_content, en_content, target_level)
        return self._make_request(prompt)

    def simplify_to_multiple_levels(self, zh_content: str, en_content: str, 
                                  levels: list = ['B1', 'A2']) -> Dict[str, str]:
        """
        Create multiple simplified versions of an article at different levels.
        
        Args:
            zh_content: Original Chinese content
            en_content: Original English content
            levels: List of CEFR levels to target
            
        Returns:
            Dictionary mapping levels to simplified content
        """
        prompt = get_multi_level_prompt(zh_content, en_content, levels)
        response = self._make_request(prompt)
        
        try:
            result = self._clean_json_response(response)
            if result:
                # Always include the original version
                result['original'] = zh_content
                return result
        except:
            pass
            
        # If multi-level simplification fails, try individual levels
        result = {'original': zh_content}
        for level in levels:
            simplified = self.simplify_article(zh_content, en_content, level)
            if simplified:
                result[level] = simplified
                
        return result
