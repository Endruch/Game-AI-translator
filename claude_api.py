"""
Claude API - Translation service with retry mechanism and error handling
"""

import logging
import time
import anthropic
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Available models in priority order (fallback if primary fails)
MODELS = [
    "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022"
]

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds


def translate_text(text: str, source_language: str, target_language: str,
                   api_key: str, max_retries: int = MAX_RETRIES) -> str:
    """
    Translate text using Claude API with retry mechanism

    Args:
        text: Text to translate
        source_language: Source language (or "Auto-detect")
        target_language: Target language
        api_key: Anthropic API key
        max_retries: Maximum number of retry attempts for transient errors

    Returns:
        Translated text or error message starting with "[Error]"
    """
    # Input validation
    if not text.strip():
        logger.warning("Empty text provided for translation")
        return ""

    if not api_key.strip():
        logger.error("API key is empty")
        return "[Error] API key is missing"

    # Build prompt
    if source_language == "Auto-detect":
        prompt = f"Translate to {target_language}. Keep player names unchanged. Return only the translation:\n\n{text}"
    else:
        prompt = f"Translate from {source_language} to {target_language}. Keep player names unchanged. Return only the translation:\n\n{text}"

    logger.info(f"Translating {len(text)} chars to {target_language}")

    # Create API client
    try:
        client = anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to create Anthropic client: {e}")
        return f"[Error] API client creation failed: {str(e)}"

    # Try each model with retry logic
    for model_index, model in enumerate(MODELS):
        logger.debug(f"Trying model: {model}")

        for retry_attempt in range(max_retries):
            try:
                # Make API call
                message = client.messages.create(
                    model=model,
                    max_tokens=1000,
                    timeout=30,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                # Extract translation
                translation = message.content[0].text.strip()
                logger.info(f"Translation success with {model}: {len(translation)} chars")
                return translation

            except anthropic.AuthenticationError as e:
                logger.error(f"Authentication failed: {e}")
                return "[Error] Invalid API key"

            except anthropic.PermissionDeniedError as e:
                logger.error(f"Permission denied: {e}")
                return "[Error] API key does not have permission"

            except anthropic.RateLimitError as e:
                logger.warning(f"Rate limit hit: {e}")
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY * (2 ** retry_attempt)  # Exponential backoff
                    logger.info(f"Retrying after {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    return "[Error] Rate limit exceeded. Please wait and try again."

            except anthropic.APIConnectionError as e:
                logger.warning(f"Connection error: {e}")
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY * (2 ** retry_attempt)
                    logger.info(f"Retrying connection after {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    return "[Error] No internet connection"

            except anthropic.APITimeoutError as e:
                logger.warning(f"API timeout: {e}")
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY
                    logger.info(f"Retrying after timeout ({delay}s)...")
                    time.sleep(delay)
                    continue
                else:
                    return "[Error] API timeout. Please try again."

            except anthropic.BadRequestError as e:
                logger.error(f"Bad request: {e}")
                return f"[Error] Invalid request: {str(e)}"

            except anthropic.NotFoundError as e:
                # Model not found, try next model
                logger.warning(f"Model {model} not found: {e}")
                break  # Break retry loop, try next model

            except anthropic.APIError as e:
                logger.error(f"API error: {e}")
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY
                    logger.info(f"Retrying after API error ({delay}s)...")
                    time.sleep(delay)
                    continue
                else:
                    return f"[Error] API error: {str(e)}"

            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY
                    logger.info(f"Retrying after unexpected error ({delay}s)...")
                    time.sleep(delay)
                    continue
                else:
                    return f"[Error] Translation failed: {str(e)}"

    # All models failed
    logger.error("All models failed to translate")
    return "[Error] Translation failed with all available models"
