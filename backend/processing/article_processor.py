from typing import Dict, Optional
import os

from processing_utils.entity_extractor import EntityExtractor
from processing_utils.segmenter import Segmenter
from processing_utils.grader import Grader
from processing_utils.simplifier import Simplifier
from processing_utils.metadata_manager import WordMetadataManager
from backend.article.processed_article import ProcessedArticle
from backend.article.article import Article

class ArticleProcessor:
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.segmenter = Segmenter()
        self.grader = Grader()
        self.simplifier = Simplifier()
        self.word_metadata_manager = WordMetadataManager()
        
    def process_article(self, article: Article) -> ProcessedArticle:
        """
        Processes an Article object and returns a ProcessedArticle object
        with segmented content and word metadata.
        """
        # Initialize the ProcessedArticle
        processed_article = ProcessedArticle.from_article(article)

        # Step 1: Extract Entities
        entities = self.entity_extractor.extract_entities(article.mandarin_content)
        processed_article.update_word_metadata(entities)

        # Step 2: Segment the Native Content
        native_segments = self.segmenter.segment_text(article.mandarin_content, custom_words=entities.keys())
        processed_article.set_version_content("native", native_segments)

        # Step 3: Grade the Words
        unique_words = set(native_segments)  # this is a list: ["你好", "世界"]
        word_levels = self.grader.tag_words(unique_words)  # this is a dict: {"你好": "A1", "世界": "A2"}
        processed_article.update_word_metadata_from_grades(word_levels)

        # Step 4: Simplify the Text
        simplified_content = self.simplifier.simplify_to_multiple_levels(processed_article)

        # Step 5: Now we segment, grade, and update metadata for simplified versions
        for version in ["beginner", "intermediate"]:
            # 5a) Segment the new version
            simplified_segments = self.segmenter.segment_text(simplified_content[version])
            # 5b) Add segmented content to processed_article
            processed_article.set_version_content(version, simplified_segments)
            # 5c) Identify new words from this version
            new_words = set(simplified_segments) - set(native_segments)
            # 5d) Grade the new unique words
            new_word_levels = self.grader.tag_words(new_words)
            # 5e) Update metadata with the new graded words
            processed_article.update_word_metadata_from_grades(new_word_levels)

        # Step 6: Handle Missing entries in word metadata like word grading and definitions
        processed_article.word_metadata = self.word_metadata_manager.fill_in_missing_metadata(processed_article.word_metadata)

        return processed_article