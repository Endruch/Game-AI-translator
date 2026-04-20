import time
import anthropic

MODELS = [
    "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022"
]

MAX_RETRIES = 3
RETRY_DELAY = 1.0


def translate_text(text: str, source_language: str, target_language: str,
                   api_key: str, max_retries: int = MAX_RETRIES) -> str:
    if not text.strip():
        return ""

    if not api_key.strip():
        return "[Error] API key is missing"

    if source_language == "Auto-detect":
        prompt = f"Translate to {target_language}. Keep player names unchanged. Return only the translation:\n\n{text}"
    else:
        prompt = f"Translate from {source_language} to {target_language}. Keep player names unchanged. Return only the translation:\n\n{text}"

    try:
        client = anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        return f"[Error] API client creation failed: {str(e)}"

    for model_index, model in enumerate(MODELS):
        for retry_attempt in range(max_retries):
            try:
                message = client.messages.create(
                    model=model,
                    max_tokens=1000,
                    timeout=30,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                translation = message.content[0].text.strip()
                return translation

            except anthropic.AuthenticationError:
                return "[Error] Invalid API key"

            except anthropic.PermissionDeniedError:
                return "[Error] API key does not have permission"

            except anthropic.RateLimitError:
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY * (2 ** retry_attempt)
                    time.sleep(delay)
                    continue
                else:
                    return "[Error] Rate limit exceeded. Please wait and try again."

            except anthropic.APIConnectionError:
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY * (2 ** retry_attempt)
                    time.sleep(delay)
                    continue
                else:
                    return "[Error] No internet connection"

            except anthropic.APITimeoutError:
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY
                    time.sleep(delay)
                    continue
                else:
                    return "[Error] API timeout. Please try again."

            except anthropic.BadRequestError as e:
                return f"[Error] Invalid request: {str(e)}"

            except anthropic.NotFoundError:
                break

            except anthropic.APIError:
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY
                    time.sleep(delay)
                    continue
                else:
                    return f"[Error] API error"

            except Exception as e:
                if retry_attempt < max_retries - 1:
                    delay = RETRY_DELAY
                    time.sleep(delay)
                    continue
                else:
                    return f"[Error] Translation failed: {str(e)}"

    return "[Error] Translation failed with all available models"
