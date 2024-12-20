from typing import Dict, Optional, List
from ..utils.llm_client import LLMClient
from ..article.article import Article

class ArticleSimplifier:
    """
    Handles the simplification of articles to different difficulty levels.
    Works with Article objects and processes their full content.
    """
    
    def __init__(self):
        """Initialize the article simplifier."""
        self.llm_client = LLMClient()
        # Map our internal level names to CEFR levels
        self.level_mapping = {
            'BEGINNER': 'A2',
            'INTERMEDIATE': 'B1'
        }

    def simplify_article(self, article: Article) -> None:
        """
        Process an article, creating simplified versions at different difficulty levels.
        Updates the article's graded_content with simplified versions.
        
        Args:
            article: Article object to simplify
        """
        # Get simplified versions for each difficulty level
        simplified_versions = self.llm_client.simplify_to_multiple_levels(
            zh_content=article.mandarin_content,
            en_content=article.english_content,
            levels=list(self.level_mapping.values())
        )
        
        # Map the simplified versions to our internal level names and add to article
        if simplified_versions:
            for internal_level, cefr_level in self.level_mapping.items():
                if cefr_level in simplified_versions:
                    article.add_graded_version(internal_level, simplified_versions[cefr_level])

    def process_article_batch(self, articles: List[Article]) -> None:
        """
        Process a batch of articles, creating simplified versions for each.
        Updates each article's graded_content with simplified versions.
        
        Args:
            articles: List of Article objects to process
        """
        for article in articles:
            try:
                self.simplify_article(article)
            except Exception as e:
                print(f"Error processing article {article.article_id}: {e}")
                continue
