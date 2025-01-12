import os
import json
import requests
from typing import Optional, Callable
from logging import logging

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Custom exception classes
class LLMClientError(Exception):
    """Base exception for LLMClient errors."""
    pass

class APIRequestError(LLMClientError):
    """Exception for API request errors."""
    pass

class ValidationError(LLMClientError):
    """Exception for response validation errors."""
    pass

class LLMClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set")

    def make_request(
        self,
        prompt: str,
        model: str = "openai/gpt-4o-mini",
        temperature: float = 0.1,
        validate_response: Optional[Callable[[str], bool]] = None,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Make a request to the OpenRouter API with retry logic and optional response validation.

        Args:
            prompt: The prompt to send to the LLM.
            model: The model to use for the request.
            temperature: The temperature setting for the LLM.
            validate_response: An optional function to validate the LLM's response.
            max_retries: The maximum number of retry attempts.

        Returns:
            The response content from the LLM, or None if the request fails.

        Raises:
            APIRequestError: If the API request fails after retries.
            ValidationError: If the response validation fails.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://xuexinwen.com",
        }

        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=headers, json=data)
                response.raise_for_status()  # Raise HTTPError for bad status codes
                content = response.json()["choices"][0]["message"]["content"]

                # Validate the response if a validation function is provided
                if validate_response and not validate_response(content):
                    logger.error(f"Validation failed on attempt {attempt + 1}")
                    raise ValidationError(f"Validation failed on attempt {attempt + 1}")

                return content

            except requests.RequestException as e:
                logger.error(f"API request failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise APIRequestError(f"API request failed after {max_retries} attempts") from e

            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON response")
                raise ValidationError("Failed to parse JSON response") from e