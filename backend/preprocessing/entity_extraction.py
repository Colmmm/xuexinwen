from typing import Dict, List
from ..utils.llm_client import LLMClient

class EntityExtractor:
    def __init__(self):
        self.llm_client = LLMClient()
        self.type_mapping = {
            "person": "names",
            "place": "places",
            "organization": "organizations",
            "other": "misc"
        }

    def extract_entities(self, article: 'Article') -> Dict[str, Dict[str, str]]:
        """
        Extract entities from an Article object.
        
        Args:
            article: Article object containing mandarin and english content
            
        Returns:
            Dictionary with entity types as keys and dictionaries of {entity: definition} as values
        """
        # Initialize result structure
        result = {
            "names": {},
            "places": {},
            "organizations": {},
            "misc": {}
        }
        
        # Get entities from LLM
        entities = self.llm_client.extract_entities(article.mandarin_content, article.english_content)
        
        if not entities:
            return result
            
        # Process each entity
        for entity in entities:
            word = entity.get("word")
            entity_type = entity.get("type")
            english_def = entity.get("english", "")
            
            if not all([word, entity_type, english_def]):
                continue
                
            # Map the entity type to our internal categories
            category = self.type_mapping.get(entity_type)
            if category:
                result[category][word] = english_def
                
        return result

    def get_all_entities(self, entities_dict: Dict[str, Dict[str, str]]) -> List[str]:
        """
        Get a flat list of all entity words from the entities dictionary.
        
        Args:
            entities_dict: The dictionary returned by extract_entities
            
        Returns:
            List of all entity words
        """
        all_entities = []
        for category in entities_dict.values():
            all_entities.extend(category.keys())
        return all_entities
