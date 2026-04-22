import io
import base64
import time
from PIL import Image

AI_PROVIDERS = {
    "Claude": {
        "name": "Claude (Anthropic)",
        "url": "https://console.anthropic.com/settings/keys",
        "models": [
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022"
        ]
    },
    "ChatGPT": {
        "name": "ChatGPT (OpenAI)",
        "url": "https://platform.openai.com/api-keys",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo"
        ]
    },
    "Grok": {
        "name": "Grok (xAI)",
        "url": "https://console.x.ai",
        "models": [
            "grok-2-vision-1212",
            "grok-vision-beta"
        ]
    },
    "DeepSeek": {
        "name": "DeepSeek",
        "url": "https://platform.deepseek.com/api_keys",
        "models": [
            "deepseek-chat"
        ]
    },
    "Gemini": {
        "name": "Gemini (Google)",
        "url": "https://aistudio.google.com/app/apikey",
        "models": [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]
    }
}


def recognize_and_translate_claude(screenshot_b64: str, source_language: str, target_language: str,
                                    api_key: str, model: str, max_retries: int = 3) -> tuple[str, str]:
    import anthropic

    if source_language == "Auto-detect":
        prompt = f"Extract all text from this image and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."
    else:
        prompt = f"Extract all text from this image (it's in {source_language}) and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."

    client = anthropic.Anthropic(api_key=api_key)

    for retry in range(max_retries):
        try:
            message = client.messages.create(
                model=model,
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            translation = message.content[0].text.strip()
            return translation, translation
        except Exception as e:
            if retry < max_retries - 1:
                time.sleep(1)
                continue
            return "", f"[Error] {str(e)}"

    return "", "[Error] Failed after retries"


def recognize_and_translate_chatgpt(screenshot_b64: str, source_language: str, target_language: str,
                                     api_key: str, model: str, max_retries: int = 3) -> tuple[str, str]:
    import openai

    if source_language == "Auto-detect":
        prompt = f"Extract all text from this image and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."
    else:
        prompt = f"Extract all text from this image (it's in {source_language}) and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."

    client = openai.OpenAI(api_key=api_key)

    for retry in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            translation = response.choices[0].message.content.strip()
            return translation, translation
        except Exception as e:
            if retry < max_retries - 1:
                time.sleep(1)
                continue
            return "", f"[Error] {str(e)}"

    return "", "[Error] Failed after retries"


def recognize_and_translate_grok(screenshot_b64: str, source_language: str, target_language: str,
                                  api_key: str, model: str, max_retries: int = 3) -> tuple[str, str]:
    import openai

    if source_language == "Auto-detect":
        prompt = f"Extract all text from this image and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."
    else:
        prompt = f"Extract all text from this image (it's in {source_language}) and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."

    client = openai.OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

    for retry in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            translation = response.choices[0].message.content.strip()
            return translation, translation
        except Exception as e:
            if retry < max_retries - 1:
                time.sleep(1)
                continue
            return "", f"[Error] {str(e)}"

    return "", "[Error] Failed after retries"


def recognize_and_translate_deepseek(screenshot_b64: str, source_language: str, target_language: str,
                                      api_key: str, model: str, max_retries: int = 3) -> tuple[str, str]:
    import openai

    if source_language == "Auto-detect":
        prompt = f"Extract all text from this image and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."
    else:
        prompt = f"Extract all text from this image (it's in {source_language}) and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."

    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    for retry in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            translation = response.choices[0].message.content.strip()
            return translation, translation
        except Exception as e:
            if retry < max_retries - 1:
                time.sleep(1)
                continue
            return "", f"[Error] {str(e)}"

    return "", "[Error] Failed after retries"


def recognize_and_translate_gemini(screenshot_b64: str, source_language: str, target_language: str,
                                    api_key: str, model: str, max_retries: int = 3) -> tuple[str, str]:
    import requests

    if source_language == "Auto-detect":
        prompt = f"Extract all text from this image and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."
    else:
        prompt = f"Extract all text from this image (it's in {source_language}) and translate it to {target_language}. Keep player names unchanged. Return ONLY the translated text, nothing else."

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": screenshot_b64
                    }
                }
            ]
        }]
    }

    for retry in range(max_retries):
        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            translation = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            return translation, translation
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg = error_data["error"].get("message", error_msg)
            except:
                pass
            if retry < max_retries - 1:
                time.sleep(1)
                continue
            return "", f"[Error] {error_msg}"
        except Exception as e:
            if retry < max_retries - 1:
                time.sleep(1)
                continue
            return "", f"[Error] {str(e)}"

    return "", "[Error] Failed after retries"


def recognize_and_translate(screenshot_b64: str, source_language: str, target_language: str,
                            provider: str, api_key: str, model: str) -> tuple[str, str]:
    if not screenshot_b64:
        return "", "[Error] Screenshot is empty"

    if not api_key.strip():
        return "", "[Error] API key is missing"

    try:
        if provider == "Claude":
            return recognize_and_translate_claude(screenshot_b64, source_language, target_language, api_key, model)
        elif provider == "ChatGPT":
            return recognize_and_translate_chatgpt(screenshot_b64, source_language, target_language, api_key, model)
        elif provider == "Grok":
            return recognize_and_translate_grok(screenshot_b64, source_language, target_language, api_key, model)
        elif provider == "DeepSeek":
            return recognize_and_translate_deepseek(screenshot_b64, source_language, target_language, api_key, model)
        elif provider == "Gemini":
            return recognize_and_translate_gemini(screenshot_b64, source_language, target_language, api_key, model)
        else:
            return "", f"[Error] Unknown provider: {provider}"
    except Exception as e:
        return "", f"[Error] {str(e)}"
