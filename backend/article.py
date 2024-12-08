from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class ArticleSection:
    """
    Represents a section (paragraph) of an article with its translations and graded versions.
    
    Attributes:
        mandarin: Original text in Mandarin Chinese
        english: English translation of the text
        graded: Dictionary containing graded versions at different difficulty levels
                Keys: 'BEGINNER', 'INTERMEDIATE'
                Values: graded text at each level
    """
    mandarin: str
    english: str
    graded: Dict[str, str] = None  # Key: difficulty level, Value: graded text

    def add_graded_version(self, level: str, text: str) -> None:
        """Add a graded version of this section at specified difficulty level."""
        if self.graded is None:
            self.graded = {}
        self.graded[level] = text

@dataclass
class Article:
    """
    Core data structure representing a news article.
    
    Attributes:
        article_id: Unique identifier for the article
        url: Source URL of the article
        date: Publication date
        source: News source identifier (e.g., 'nyt', 'bbc')
        authors: List of article authors
        
        mandarin_title: Article title in Mandarin Chinese
        english_title: Article title in English
        
        sections: List of ArticleSection objects containing the article content
        
        metadata: Additional metadata about the article
    """
    article_id: str
    url: str
    date: datetime
    source: str
    authors: List[str]
    mandarin_title: str
    english_title: str
    sections: List[ArticleSection]
    image_url: Optional[str]
    metadata: Dict = None
    
    @property
    def mandarin_content(self) -> str:
        """Get full article content in Mandarin Chinese."""
        return "\n\n".join(section.mandarin for section in self.sections)
    
    @property
    def english_content(self) -> str:
        """Get full article content in English."""
        return "\n\n".join(section.english for section in self.sections)
    
    def get_graded_content(self, level: str) -> Optional[str]:
        """
        Get full article content at specified difficulty level.
        
        Args:
            level: Difficulty level ('BEGINNER', 'INTERMEDIATE', or 'native')
            
        Returns:
            Optional[str]: The graded content if available, None otherwise
        """
        if level == 'native':
            return self.mandarin_content
            
        if not all(section.graded and level in section.graded 
                  for section in self.sections):
            return None
        return "\n\n".join(section.graded[level] for section in self.sections)
    
    def to_dict(self) -> Dict:
        """Convert article to dictionary representation."""
        return {
            'article_id': self.article_id,
            'url': self.url,
            'date': self.date.isoformat(),
            'source': self.source,
            'authors': self.authors,
            'mandarin_title': self.mandarin_title,
            'english_title': self.english_title,
            'image_url': self.image_url,
            'sections': [
                {
                    'mandarin': section.mandarin,
                    'english': section.english,
                    'graded': section.graded
                }
                for section in self.sections
            ],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Article':
        """Create Article instance from dictionary representation."""
        sections = [
            ArticleSection(
                mandarin=section['mandarin'],
                english=section['english'],
                graded=section.get('graded')
            )
            for section in data['sections']
        ]
        
        return cls(
            article_id=data['article_id'],
            url=data['url'],
            date=datetime.fromisoformat(data['date']),
            source=data['source'],
            authors=data['authors'],
            mandarin_title=data['mandarin_title'],
            english_title=data['english_title'],
            sections=sections,
            image_url=data.get('image_url'),
            metadata=data.get('metadata')
        )
