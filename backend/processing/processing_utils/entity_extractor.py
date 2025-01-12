from typing import Dict, List, Optional
from processing_utils.prompts.entity_extraction_prompt import get_entity_extraction_prompt
from processing_utils.llm_client import LLMClient, APIRequestError, ValidationError
import json
import logging

logger = logging.getLogger(__name__)

class EntityExtractor:
    def __init__(self):
        self.llm_client = LLMClient()

    def extract_entities(self, mandarin_content: str, english_content: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """
        Extract entities from Mandarin content using LLM, with optional English content for context, returning a metadata dictionary for each entity.
        """
        # Generate the prompt
        prompt = get_entity_extraction_prompt(mandarin_content, english_content)

        # Define a validation function for the LLM response
        def validate_entities_response(response: str) -> bool:
            try:
                entities = json.loads(response)
                if not isinstance(entities, list):
                    return False
                # Ensure each entity is a dict with the expected keys
                expected_keys = {"simplified", "traditional", "grade", "definition", "pinyin", "entity_type"}
                return all(isinstance(entity, dict) and expected_keys.issubset(entity.keys()) for entity in entities)
            except json.JSONDecodeError:
                return False

        try:
            # Get raw response from LLM with retry logic
            response = self.llm_client.make_request(prompt, validate_response=validate_entities_response)
            if not response:
                logger.error("No response from LLM after retries.")
                return {}

            # Parse the valid response
            entities = json.loads(response)

            # Process each entity and construct the metadata dictionary
            entity_metadata = {}
            for entity in entities:
                word = entity.get("simplified")
                entity_metadata[word] = {
                    "simplified": entity.get("simplified", ""),
                    "traditional": entity.get("traditional", ""),
                    "grade": entity.get("grade", "unknown"),
                    "definition": entity.get("definition", ""),
                    "pinyin": entity.get("pinyin", ""),
                    "entity_type": entity.get("entity_type", "misc"),
                }

            return entity_metadata

        except APIRequestError as e:
            logger.error(f"API request failed: {e}")
            return {}

        except ValidationError as e:
            logger.error(f"Response validation error: {e}")
            return {}

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response after validation.")
            return {}
