from typing import Dict, Set, List, Optional
import pandas as pd
from collections import OrderedDict
import jieba
from ..utils.llm_client import LLMClient
from ..article.article import Article

class TOCFLTagger:
    def __init__(self, tocfl_csv_path: str):
        """
        Initialize the TOCFL tagger with a dictionary file.
        
        Args:
            tocfl_csv_path: Path to the TOCFL CSV dictionary file
        """
        self.word_dict = self._load_tocfl_dictionary(tocfl_csv_path)
        self.llm_client = LLMClient()
        self.cefr_levels = ['A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'unknown']

    def _load_tocfl_dictionary(self, tocfl_csv_path: str) -> Dict[str, Dict[str, str]]:
        """
        Load TOCFL dictionary and add words to Jieba.
        
        Args:
            tocfl_csv_path: Path to the TOCFL CSV dictionary file
            
        Returns:
            Dictionary mapping both traditional and simplified characters to their level
        """
        df = pd.read_csv(tocfl_csv_path)
        word_dict = {}
        
        for _, row in df.iterrows():
            # Map both traditional and simplified to the simplified form and level
            word_dict[row['traditional']] = {
                'level': row['cefr_level'],
                'simplified': row['simplified']
            }
            word_dict[row['simplified']] = {
                'level': row['cefr_level'],
                'simplified': row['simplified']
            }
            
            # Add both forms to Jieba
            jieba.add_word(row['traditional'], freq=1000)
            jieba.add_word(row['simplified'], freq=1000)
        
        return word_dict

    def create_ordered_dict(self) -> OrderedDict:
        """Create an ordered dictionary with CEFR levels in correct order."""
        return OrderedDict((level, set()) for level in self.cefr_levels)

    def get_word_info(self, word: str) -> Optional[Dict[str, str]]:
        """
        Get TOCFL information for a word.
        
        Args:
            word: Chinese word to look up
            
        Returns:
            Dictionary with level and simplified form, or None if not found
        """
        return self.word_dict.get(word)

    def classify_unknown_words(self, unknown_words: Set[str]) -> Dict[str, str]:
        """
        Classify unknown words into CEFR levels using LLM.
        
        Args:
            unknown_words: Set of words not found in TOCFL dictionary
            
        Returns:
            Dictionary mapping words to their predicted CEFR levels
        """
        if not unknown_words:
            return {}
            
        return self.llm_client.classify_words(list(unknown_words))

    def categorize_words(self, words: List[str]) -> Dict[str, List[str]]:
        """
        Categorize a list of words by CEFR level.
        
        Args:
            words: List of Chinese words to categorize
            
        Returns:
            Dictionary mapping CEFR levels to lists of words
        """
        result = self.create_ordered_dict()
        unknown_words = set()
        
        # First pass: categorize known words
        for word in words:
            word_info = self.get_word_info(word)
            if word_info:
                level = word_info['level']
                result[level].add(word_info['simplified'])
            else:
                unknown_words.add(word)
        
        # Classify unknown words
        if unknown_words:
            classifications = self.classify_unknown_words(unknown_words)
            for word, level in classifications.items():
                result[level].add(word)
                # Remove from unknown category if successfully classified
                if word in unknown_words:
                    unknown_words.remove(word)
        
        # Add remaining unknown words
        for word in unknown_words:
            result['unknown'].add(word)
        
        # Convert sets to sorted lists
        return {
            level: sorted(list(words))
            for level, words in result.items()
            if words  # Only include non-empty levels
        }

    def get_word_level_map(self, words: List[str]) -> Dict[str, str]:
        """
        Create a flat dictionary mapping words to their CEFR levels.
        
        Args:
            words: List of Chinese words to categorize
            
        Returns:
            Dictionary mapping words to their CEFR levels
        """
        word_level_map = {}
        unknown_words = set()
        
        # First pass: map known words
        for word in words:
            word_info = self.get_word_info(word)
            if word_info:
                word_level_map[word] = word_info['level']
            else:
                unknown_words.add(word)
        
        # Classify unknown words
        if unknown_words:
            classifications = self.classify_unknown_words(unknown_words)
            word_level_map.update(classifications)
            
            # Add remaining words as unknown
            for word in unknown_words:
                if word not in classifications:
                    word_level_map[word] = 'unknown'
        
        return word_level_map
