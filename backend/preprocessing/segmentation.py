from typing import List, Dict, Optional
import jieba
import re
from ..article.article import Article

class Segmenter:
    def __init__(self):
        """Initialize the segmenter and ensure Jieba is loaded."""
        jieba.initialize()

    def _clean_word(self, word: str) -> Optional[str]:
        """
        Clean word by removing punctuation and whitespace.
        
        Args:
            word: Word to clean
            
        Returns:
            Cleaned word or None if word is only punctuation/whitespace
        """
        word = word.strip()
        if re.match(r'^[\s\W]+$', word):
            return None
        return word

    def add_words_to_dictionary(self, words: List[str], freq: int = 1000):
        """
        Add words to Jieba's custom dictionary.
        
        Args:
            words: List of words to add
            freq: Frequency to assign to the words
        """
        for word in words:
            jieba.add_word(word, freq=freq)

    def segment_text(self, text: str, custom_words: List[str] = None) -> List[str]:
        """
        Segment Chinese text into words using Jieba.
        
        Args:
            text: Chinese text to segment
            custom_words: Optional list of custom words to add to dictionary
            
        Returns:
            List of segmented words with punctuation and empty strings removed
        """
        # Add any custom words to the dictionary
        if custom_words:
            self.add_words_to_dictionary(custom_words)
        
        # Segment the text
        words = jieba.cut(text, cut_all=False)
        
        # Clean and filter words
        cleaned_words = []
        for word in words:
            cleaned = self._clean_word(word)
            if cleaned:
                cleaned_words.append(cleaned)
                
        return cleaned_words

    def segment_article(self, article: Article, custom_words: List[str] = None) -> Dict[str, List[str]]:
        """
        Segment an article's content and its graded versions.
        
        Args:
            article: Article object to segment
            custom_words: Optional list of custom words to add to dictionary
            
        Returns:
            Dictionary mapping content levels to their segmented words
        """
        # Initialize result with original content
        result = {
            'native': self.segment_text(article.mandarin_content, custom_words)
        }
        
        # Process graded versions if they exist
        if article.graded_content:
            for level, content in article.graded_content.items():
                result[level] = self.segment_text(content, custom_words)
                
        return result

    def get_sentence_boundaries(self, text: str) -> List[tuple]:
        """
        Get the start and end indices of sentences in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of (start, end) tuples marking sentence boundaries
        """
        # Find all sentence-ending punctuation
        boundaries = []
        start = 0
        
        # Pattern for sentence endings (。！？followed by optional whitespace)
        pattern = r'[。！？][\s]*'
        
        for match in re.finditer(pattern, text):
            end = match.end()
            if end > start:  # Only add non-empty sentences
                boundaries.append((start, end))
            start = end
            
        # Add the last segment if it doesn't end with punctuation
        if start < len(text):
            boundaries.append((start, len(text)))
            
        return boundaries
