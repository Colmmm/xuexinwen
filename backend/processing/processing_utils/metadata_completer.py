from typing import Dict
from ...article.processed_article import ProcessedArticle, WordMetadata
import cedict_utils.cedict as cedict

class MetadataCompleter:
    """
    Completes missing word metadata such as definitions, grades, and pinyin
    using external resources like CC-CEDICT.
    """

    def __init__(self, cedict_path: str):
        self.cedict = cedict.read_cedict(cedict_path)

    def fill_in_missing_metadata(self, word_metadata: Dict[str, WordMetadata]) -> Dict[str, WordMetadata]:
        """
        Completes missing metadata entries such as definitions and grades.

        Args:
            word_metadata: Dictionary of word metadata to complete.

        Returns:
            Updated dictionary with missing metadata filled in.
        """
        for word, metadata in word_metadata.items():
            if not metadata.definition:
                entry = self._get_cedict_entry(word)
                if entry:
                    metadata.definition = "; ".join(entry["definitions"])
                    metadata.traditional = entry["traditional"]
                    metadata.pinyin = entry["pinyin"]
        return word_metadata

    def _get_cedict_entry(self, word: str) -> Dict[str, str]:
        """
        Retrieves a word entry from CC-CEDICT.

        Args:
            word: The word to look up.

        Returns:
            Dictionary with traditional form, pinyin, and definitions if found.
        """
        entries = self.cedict.get(word, [])
        if entries:
            return entries[0]
        return {}
