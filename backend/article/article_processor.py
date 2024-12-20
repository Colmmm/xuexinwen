from typing import Dict, Optional
import os

from ..preprocessing.entity_extraction import EntityExtractor
from ..preprocessing.tocfl_tagger import TOCFLTagger
from ..preprocessing.segmentation import Segmenter
from ..postprocessing.html_wrapper import HTMLWrapper
from ..main_processing.simplify_articles import ArticleSimplifier
from .article import Article

class ArticleProcessor:
    def __init__(self, tocfl_csv_path: str):
        """
        Initialize the article processor with necessary components.
        
        Args:
            tocfl_csv_path: Path to the TOCFL CSV dictionary file
        """
        # Initialize components
        self.entity_extractor = EntityExtractor()
        self.tocfl_tagger = TOCFLTagger(tocfl_csv_path)
        self.segmenter = Segmenter()
        self.html_wrapper = HTMLWrapper()
        self.article_simplifier = ArticleSimplifier()

    def process_article(self, article: Article, simplify: bool = True) -> Dict:
        """
        Process an article through all stages: entity extraction, segmentation,
        TOCFL tagging, simplification (optional), and HTML wrapping.
        
        Args:
            article: Article object to process
            simplify: Whether to create simplified versions
            
        Returns:
            Dictionary containing processed article data:
            {
                'html_content': str,  # HTML-wrapped content
                'entities': {         # Extracted entities by type
                    'names': {...},
                    'places': {...},
                    'organizations': {...},
                    'misc': {...}
                },
                'word_levels': {...}  # Word to CEFR level mapping
            }
        """
        # 1. Extract entities
        entities = self.entity_extractor.extract_entities(article)
        
        # 2. Get all entity words for custom dictionary
        entity_words = self.entity_extractor.get_all_entities(entities)
        
        # 3. Segment all versions of the text, using entities as custom dictionary words
        segmented_versions = self.segmenter.segment_article(
            article=article,
            custom_words=entity_words
        )
        
        # Get the words from the original content for TOCFL tagging
        words = segmented_versions['native']
        
        # 4. Get word level mapping
        word_level_map = self.tocfl_tagger.get_word_level_map(words)
        
        # 5. Create categorized word levels for statistics/analysis
        word_levels = self.tocfl_tagger.categorize_words(words)
        
        # 6. Optionally create simplified versions
        if simplify:
            self.article_simplifier.simplify_article(article)
            
        # 7. Generate HTML with wrapped words for all versions
        html_versions = {}
        for level, segmented_words in segmented_versions.items():
            html_versions[level] = self.html_wrapper.process_text(
                words=segmented_words,
                word_levels=word_level_map,
                entity_definitions=entities
            )
        
        return {
            'html_versions': html_versions,
            'entities': entities,
            'word_levels': word_levels
        }

    def process_batch(self, articles: list[Article], simplify: bool = True) -> list[Dict]:
        """
        Process a batch of articles.
        
        Args:
            articles: List of Article objects to process
            simplify: Whether to create simplified versions
            
        Returns:
            List of processed article data
        """
        results = []
        for article in articles:
            try:
                result = self.process_article(article, simplify)
                results.append(result)
            except Exception as e:
                print(f"Error processing article {article.article_id}: {e}")
                continue
        return results
