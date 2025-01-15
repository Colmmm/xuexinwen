from typing import Dict, List, Union, Optional
from datetime import datetime
from dataclasses import dataclass
from article import Article

# Type for version names
VersionType = Literal["native", "intermediate", "beginner"]

# Type for entity types
EntityType = Literal["person", "location", "organization", "misc", False]

# Type for CEFR-like grades
GradeType = Literal["A0", "A1", "A2", "B1", "B2", "C1", "C2"]

@dataclass
class WordMetadata:
    """Metadata for a single word/phrase in the article."""
    simplified: str
    traditional: str
    grade: GradeType
    definition: str
    pinyin: str
    entity_type: EntityType
    presence_in_versions: List[VersionType]

class WordMetadataCollection:
    """
    A helper class to manage multiple WordMetadata objects.
    """
    def __init__(self):
        self._metadata: Dict[str, WordMetadata] = {}

    def add_or_update_metadata(self, metadata: WordMetadata) -> None:
        word = metadata.simplified
        if word in self._metadata:
            existing_metadata = self._metadata[word]
            existing_metadata.presence_in_versions.extend(
                version for version in metadata.presence_in_versions
                if version not in existing_metadata.presence_in_versions
            )
        else:
            self._metadata[word] = metadata

    def get_metadata(self, word: str) -> Optional[WordMetadata]:
        return self._metadata.get(word)

    def get_all_metadata(self) -> Dict[str, WordMetadata]:
        return self._metadata

    def merge(self, new_metadata: WordMetadataCollection) -> None:
        for metadata in new_metadata.get_all_metadata().values():
            self.add_or_update_metadata(metadata)

@dataclass
class ProcessedArticle(Article):
    """
    Represents a processed article that extends the base Article class with
    segmented content for different proficiency levels and comprehensive word metadata.
    """
    segmented_content: Dict[VersionType, List[str]]
    word_metadata: WordMetadataCollection

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.segmented_content = {"native": [], "intermediate": [], "beginner": []}
        self.word_metadata = WordMetadataCollection()  # Updated to use the new collection class

    def update_word_metadata(self, new_metadata: WordMetadataCollection) -> None:
        """
        Update word metadata.

        Args:
            new_metadata: A collection of new WordMetadata objects to add or update.
        """
        self.word_metadata.merge(new_metadata)

    def set_version_content(self, version: VersionType, content: List[str]) -> None:
        self.segmented_content[version] = content

    def get_version_content(self, version: VersionType) -> List[str]:
        return self.segmented_content[version]

    def get_word_metadata(self, word: str) -> Union[WordMetadata, None]:
        return self.word_metadata.get_metadata(word)

    def get_entities(self) -> List[Dict[str, str]]:
        entities = []
        for metadata in self.word_metadata.get_all_metadata().values():
            if metadata.entity_type:
                entities.append({
                    "simplified": metadata.simplified,
                    "traditional": metadata.traditional,
                    "entity_type": metadata.entity_type,
                    "definition": metadata.definition
                })
        return entities

    def get_word_grading_lists(self) -> Dict[str, List[str]]:
        gradings = {level: [] for level in ["A0", "A1", "A2", "B1", "B2", "C1", "C2", "unknown"]}
        for metadata in self.word_metadata.get_all_metadata().values():
            gradings[metadata.grade].append(metadata.simplified)
        return gradings

    def to_dict(self) -> Dict:
        base_dict = super().to_dict()
        return {
            **base_dict,
            'segmented_content': self.segmented_content,
            'word_metadata': {
                word: {
                    'simplified': meta.simplified,
                    'traditional': meta.traditional,
                    'grade': meta.grade,
                    'definition': meta.definition,
                    'pinyin': meta.pinyin,
                    'entity_type': meta.entity_type,
                    'presence_in_versions': meta.presence_in_versions
                } for word, meta in self.word_metadata.get_all_metadata().items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ProcessedArticle':
        instance = super().from_dict(data)
        instance.segmented_content = data.get('segmented_content', {"native": [], "intermediate": [], "beginner": []})
        instance.word_metadata = WordMetadataCollection()
        for meta in data.get('word_metadata', {}).values():
            instance.word_metadata.add_or_update_metadata(WordMetadata(
                simplified=meta['simplified'],
                traditional=meta['traditional'],
                grade=meta['grade'],
                definition=meta['definition'],
                pinyin=meta['pinyin'],
                entity_type=meta['entity_type'],
                presence_in_versions=meta['presence_in_versions']
            ))
        return instance
