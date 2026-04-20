import anthropic

MODELS = ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]


def translate_text(text: str, source_language: str, target_language: str, api_key: str) -> str:
    if not text.strip():
        return ""
    if not api_key.strip():
        return "[Error] Enter API key in Settings"

    prompt = f"Translate to {target_language}. Keep player names. Return only translation:\n\n{text}"
    client = anthropic.Anthropic(api_key=api_key)

    for model in MODELS:
        try:
            message = client.messages.create(model=model, max_tokens=1000, timeout=30, messages=[{"role": "user", "content": prompt}])
            return message.content[0].text.strip()
        except anthropic.AuthenticationError:
            return "[Error] Invalid API key"
        except anthropic.RateLimitError:
            return "[Error] Rate limit"
        except anthropic.APIConnectionError:
            return "[Error] No internet"
        except (anthropic.NotFoundError, Exception):
            continue

    return "[Error] Translation failed"
