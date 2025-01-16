from typing import Dict, List, Optional
from backend.processing.processing_utils.prompts.simplification_prompt import get_simplification_prompt
from .llm_client import LLMClient, APIRequestError, ValidationError
import json
from backend.logger.logger import setup_logger
from backend.article.processed_article import ProcessedArticle
logger = setup_logger(__name__)

class Simplifier:
    """
    Simplifies Chinese articles to different CEFR levels using a language model.
    """

    def __init__(self):
        self.llm_client = LLMClient()

    def simplify(self, article: ProcessedArticle) -> Dict[str, str]:
        """
        Simplifies an article into beginner and intermediate levels using the LLM client.

        Args:
            article: ProcessedArticle object containing the original native content.

        Returns:
            A dictionary with simplified versions for 'beginner' and 'intermediate'.
        """

        # Generate the prompt
        prompt = get_simplification_prompt(
          article.mandarin_content,
          article.mandarin_title,
          article.english_content,
          article.english_title,
          article.get_entities(),
          article.get_word_grading_lists()
        )

        # Define a validation function for the LLM response
        def validate_simplification_response(response: str) -> bool:
            try:
                versions = json.loads(response)
                if not isinstance(versions, dict):
                    return False
                expected_levels = {"beginner", "intermediate"}
                return expected_levels.issubset(versions.keys())
            except json.JSONDecodeError:
                return False

        try:
            # Get raw response from LLM with retry logic
            response = self.llm_client.make_request(prompt, validate_response=validate_simplification_response)
            if not response:
                logger.error("No response from LLM after retries.")
                return {'beginner': '', 'intermediate': ''}

            # Parse the valid response
            simplified_versions = json.loads(response)
            return {
                'beginner': simplified_versions.get('beginner', ''),
                'intermediate': simplified_versions.get('intermediate', '')
            }

        except APIRequestError as e:
            logger.error(f"API request failed: {e}")
            return {'beginner': '', 'intermediate': ''}

        except ValidationError as e:
            logger.error(f"Response validation error: {e}")
            return {'beginner': '', 'intermediate': ''}

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response after validation.")
            return {'beginner': '', 'intermediate': ''}
