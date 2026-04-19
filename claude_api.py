"""
claude_api.py - Translation logic using Claude API
Handles auto language detection and translation
"""

import anthropic


def translate_text(text: str, source_language: str, target_language: str, api_key: str) -> str:
    """
    Translates text from source_language to target_language using Claude API.
    If source_language is "Auto-detect", automatically detects the source language.
    Returns translated text or error message.
    """
    if not text.strip():
        return ""

    if not api_key.strip():
        return "[Error] API key is not set. Please open Settings."

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Build prompt based on source language setting
        if source_language == "Auto-detect":
            prompt = f"""You are a translator for an online game chat.
The chat contains messages in various languages (English, Spanish, Korean, French, German, Russian, etc.).

Your task:
1. Detect the language of each message automatically
2. Translate everything to {target_language}
3. Keep the original structure (one message per line)
4. Do NOT translate player names or game terms that are clearly proper nouns
5. If a line is already in {target_language}, keep it as is
6. Return ONLY the translated text, no explanations

Text to translate:
{text}"""
        else:
            prompt = f"""You are a translator for an online game chat.

Your task:
1. Translate the text from {source_language} to {target_language}
2. Keep the original structure (one message per line)
3. Do NOT translate player names or game terms that are clearly proper nouns
4. If a line is already in {target_language}, keep it as is
5. Return ONLY the translated text, no explanations

Text to translate:
{text}"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text.strip()

    except anthropic.AuthenticationError:
        return "[Error] Invalid API key. Please check Settings."
    except anthropic.RateLimitError:
        return "[Error] Rate limit reached. Please wait a moment."
    except anthropic.APIConnectionError:
        return "[Error] No internet connection."
    except Exception as e:
        return f"[Error] {str(e)}"
