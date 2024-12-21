from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime

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
        
        mandarin_content: Full article content in Mandarin Chinese
        english_content: Full article content in English
        mandarin_section_indices: List of (start, end) indices marking mandarin section boundaries
        english_section_indices: List of (start, end) indices marking english section boundaries
        graded_content: Dictionary containing graded versions at different difficulty levels
        
        metadata: Additional metadata about the article
    """
    article_id: str
    url: str
    date: datetime
    source: str
    authors: List[str]
    mandarin_title: str
    english_title: str
    mandarin_content: str
    english_content: str
    mandarin_section_indices: List[Tuple[int, int]]  # List of (start, end) indices for mandarin sections
    english_section_indices: List[Tuple[int, int]]  # List of (start, end) indices for english sections
    image_url: Optional[str]
    graded_content: Dict[str, str] = None  # Key: difficulty level, Value: graded text
    metadata: Dict = None

    def get_section_content(self, index: int) -> Tuple[str, str]:
        """
        Get content for a specific section.
        
        Args:
            index: Index of the section to retrieve
            
        Returns:
            tuple: (mandarin_text, english_text) for the section
        """
        if index >= len(self.mandarin_section_indices) or index >= len(self.english_section_indices):
            raise IndexError(f"Section index {index} out of range")
            
        m_start, m_end = self.mandarin_section_indices[index]
        e_start, e_end = self.english_section_indices[index]
        return (
            self.mandarin_content[m_start:m_end].strip(),
            self.english_content[e_start:e_end].strip()
        )

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
            
        return self.graded_content.get(level) if self.graded_content else None

    def add_graded_version(self, level: str, content: str) -> None:
        """
        Add a graded version of the article at specified difficulty level.
        
        Args:
            level: Difficulty level ('BEGINNER', 'INTERMEDIATE')
            content: Graded content at that level
        """
        if self.graded_content is None:
            self.graded_content = {}
        self.graded_content[level] = content

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
            'mandarin_content': self.mandarin_content,
            'english_content': self.english_content,
            'mandarin_section_indices': self.mandarin_section_indices,
            'english_section_indices': self.english_section_indices,
            'image_url': self.image_url,
            'graded_content': self.graded_content,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Article':
        """Create Article instance from dictionary representation."""
        return cls(
            article_id=data['article_id'],
            url=data['url'],
            date=datetime.fromisoformat(data['date']),
            source=data['source'],
            authors=data['authors'],
            mandarin_title=data['mandarin_title'],
            english_title=data['english_title'],
            mandarin_content=data['mandarin_content'],
            english_content=data['english_content'],
            mandarin_section_indices=data['mandarin_section_indices'],
            english_section_indices=data['english_section_indices'],
            image_url=data.get('image_url'),
            graded_content=data.get('graded_content'),
            metadata=data.get('metadata')
        )
