import httpx  # Use httpx for async HTTP requests
from typing import List, Dict

from ollama import chat, ChatResponse

class TranslationService:
    def __init__(self):
        self.lm_studio_url = "http://localhost:1234/v1/chat/completions"  # Correct endpoint
        self.ollama_url = "http://localhost:11434/api/generate"  # Correct endpoint
        self.translation_api_url = "https://api.mymemory.translated.net/get"  # Correct endpoint

    async def translate_with_openai(
            self,
            text: str,
            target_language: str = "Russian"
    ) -> str:
        """
        Translate using OpenAI-compatible API (LM Studio)

        Args:
            text: Text to translate
            target_language: Target language name (Spanish, French, etc.)

        Returns:
            Translated text
        """
        prompt = f"You are a professional translator. Translate the following text to {target_language}. Only return the translation, nothing else."

        messages = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": text
            }
        ]

        try:
            response: ChatResponse = chat(model="deepseek-r1:14b", messages=messages, stream=False)

            print(response["message"]["content"])

            # Extract the translated text from the response
            translated_text = response["message"]["content"].strip()
            return translated_text

        except httpx.HTTPError as e:
            raise Exception(f"HTTP error occurred: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {e}. Response: {result}")
        except Exception as e:
            raise Exception(f"Translation error: {e}")

    async def translate_text(self, text: str, source_lang: str = "en", target_lang: str = "ru") -> str:
        params = {
            "q": text,
            "langpair": f"{source_lang}|{target_lang}",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.translation_api_url, params=params)
                return response.json()["matches"][0]["translation"]
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error occurred: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected response format: {e}. Response: {result}")
        except Exception as e:
            raise Exception(f"Translation error: {e}")

    async def translate_segments(
            self,
            segments: List[Dict],
            target_language: str = "Russian",
    ) -> List[Dict]:
        """
        Translate each segment separately (preserves timing)

        Args:
            segments: List of segments from WhisperX
            target_language: Target language (e.g., "Spanish", "French")

        Returns:
            List of segments with translations
        """
        translated_segments = []

        for segment in segments:
            # Use await since translate_with_openai is async
            translated_text = await self.translate_text(
                segment["text"],
                "en",
                target_language
            )

            translated_segments.append({
                **segment,
                "original_text": segment["text"],
                "translated_text": translated_text
            })

        return translated_segments