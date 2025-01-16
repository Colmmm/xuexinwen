from typing import Dict, Optional
import os

from .processing_utils.entity_extractor import EntityExtractor
from .processing_utils.segmenter import Segmenter
from .processing_utils.simplifier import Simplifier
from .processing_utils.metadata_generator import MetadataGenerator
from backend.article.processed_article import ProcessedArticle
from backend.article.article import Article

class ArticleProcessor:
    def __init__(self):
        self.entity_extractor = EntityExtractor()
        self.segmenter = Segmenter()
        self.simplifier = Simplifier()
        self.metadata_generator = MetadataGenerator()
        
    def process_article(self, article: Article) -> ProcessedArticle:
        """
        Processes an Article object and returns a ProcessedArticle object
        with segmented content and word metadata.
        """
        # Initialize the ProcessedArticle
        processed_article = ProcessedArticle.from_article(article)

        # Step 1: Extract Entities
        entities_metadata = self.entity_extractor.extract_entities(article.mandarin_content)
        processed_article.update_word_metadata(entities_metadata)

        # Step 2: Segment the Native Article Content
        native_segments = self.segmenter.segment_text(article.mandarin_content, custom_words=entities_metadata.keys())
        processed_article.set_version_content("native", native_segments)

        # Step 3: Generate metadata for native article content
        native_metadata = self.metadata_generator.generate_from_segments(native_segments, 'native', processed_article.word_metadata)
        processed_article.update_word_metadata(native_metadata)
       
        # Step 4: Simplify the Text
        simplified_content = self.simplifier.simplify_to_multiple_levels(processed_article)

        # Step 5: Now we segment, grade, and update metadata for simplified versions
        for version in ["beginner", "intermediate"]:
            # 5a) Segment the new version
            simplified_segments = self.segmenter.segment_text(simplified_content[version])
            # 5b) Add segmented content to processed_article
            processed_article.set_version_content(version, simplified_segments)
            # 5c) Generate metadata for simplified version
            simplified_metadata = self.metadata_generator.generate_from_segments(simplified_segments, version, processed_article.word_metadata)
            # 5e) Update metadata from new metadata from simplified versions 
            processed_article.update_word_metadata(simplified_metadata)


        return processed_article
