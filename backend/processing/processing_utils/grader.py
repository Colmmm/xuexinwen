from typing import Dict, Set, List, Optional
import pandas as pd
import jieba
import re
from collections import OrderedDict

class Grader:
    def __init__(self, tocfl_csv_path: str):
        """
        Initialize the Grader with a TOCFL dictionary.

        Args:
            tocfl_csv_path: Path to the TOCFL CSV dictionary file.
        """
        self.word_dict = self._load_tocfl_dictionary(tocfl_csv_path)
        self.cefr_levels = ['A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2']

    def _load_tocfl_dictionary(self, tocfl_csv_path: str) -> Dict[str, Dict[str, str]]:
        """
        Load the TOCFL dictionary from a CSV file.

        Args:
            tocfl_csv_path: Path to the TOCFL CSV dictionary file.

        Returns:
            A dictionary mapping both traditional and simplified characters to their CEFR levels.
        """
        df = pd.read_csv(tocfl_csv_path)
        word_dict = {}
        
        for _, row in df.iterrows():
            word_dict[row['simplified']] = {
                'level': row['cefr_level'],
                'traditional': row['traditional']
            }
            word_dict[row['traditional']] = {
                'level': row['cefr_level'],
                'simplified': row['simplified']
            }

        return word_dict

    def tag_words(self, words: Set[str]) -> Dict[str, str]:
        """
        Tag a set of words with their corresponding CEFR levels, filtering out punctuation.

        Args:
            words: A set of words to be tagged.

        Returns:
            A dictionary mapping words to their CEFR levels.
        """
        # Filter out punctuation
        words = {word for word in words if not re.match(r'^[。，！？：；、“”‘’（）—…【】《》]+$', word)}
        
        result = {}
        for word in words:
            if word in self.word_dict:
                result[word] = self.word_dict[word]['level']
            else:
                result[word] = 'unknown'
        return result

    def classify_unknown_words(self, unknown_words: Set[str]) -> Dict[str, str]:
        """
        Classify unknown words into CEFR levels using an external classification method.

        Args:
            unknown_words: A set of words not found in the TOCFL dictionary.

        Returns:
            A dictionary mapping unknown words to their predicted CEFR levels.
        """
        # Placeholder for future implementation
        return {word: 'unknown' for word in unknown_words}

    def get_word_level_map(self, words: List[str]) -> Dict[str, str]:
        """
        Create a flat dictionary mapping words to their CEFR levels.

        Args:
            words: A list of Chinese words to categorize.

        Returns:
            A dictionary mapping words to their CEFR levels.
        """
        word_level_map = self.tag_words(set(words))
        return word_level_map
