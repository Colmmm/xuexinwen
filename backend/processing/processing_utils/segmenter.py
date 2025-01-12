from typing import List, Optional
import jieba
import re

class Segmenter:
    def __init__(self):
        """Initialize the segmenter and ensure Jieba is loaded."""
        jieba.initialize()

    def add_words_to_dictionary(self, words: List[str], freq: int = 1000):
        """
        Add words to Jieba's custom dictionary.

        Args:
            words: List of words to add
            freq: Frequency to assign to the words
        """
        for word in words:
            jieba.add_word(word, freq=freq)

    def segment_text(self, text: str, custom_words: Optional[List[str]] = None) -> List[str]:
        """
        Segment Chinese text into words using Jieba, retaining punctuation as separate segments.

        Args:
            text: Chinese text to segment
            custom_words: Optional list of custom words to add to dictionary

        Returns:
            List of segmented words with punctuation retained and empty strings removed
        """
        if custom_words:
            self.add_words_to_dictionary(custom_words)

        # Segment the text
        words = jieba.cut(text, cut_all=False)

        # Clean and filter words
        cleaned_words = [self._clean_word(word) for word in words if self._clean_word(word)]

        return cleaned_words

    def _clean_word(self, word: str) -> Optional[str]:
        """
        Clean word by removing whitespace but retaining Chinese punctuation.

        Args:
            word: Word to clean

        Returns:
            Cleaned word or None if the word is only whitespace.
        """
        cleaned = word.strip()
        if not cleaned:
            return None

        # Allow Chinese punctuation (。！？：；、“”‘’（）—…【】《》)
        if re.match(r'^[。，！？：；、“”‘’（）—…【】《》]+$', cleaned):
            return cleaned

        # Remove non-Chinese characters and whitespace
        if re.match(r'^[\s\W]+$', cleaned):
            return None

        return cleaned


