import os
import time
from dotenv import load_dotenv
from google import genai
from ragchatbot.llm.base import BaseLLM

load_dotenv()


class GeminiLLM(BaseLLM):

    def __init__(self, api_key: str = None, model: str = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        model = model or os.getenv("ragchatbot_MODEL", "gemini-2.0-flash")

        if not key:
            raise ValueError(
                "Gemini API key not found. "
                "Set GEMINI_API_KEY in your .env file or pass api_key= directly."
            )

        self.client = genai.Client(api_key=key)
        self.model = model
        print(f"Gemini ready — model: {model}")

    def generate(self, question: str, context_chunks: list[dict]) -> dict:
        if not context_chunks:
            return {
                "answer": "I don't have that information in my docs.",
                "sources": []
            }

        prompt = self._build_prompt(question, context_chunks)

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                answer = response.text.strip()
                break
            except Exception as e:
                error = str(e)
                if "429" in error and attempt < 2:
                    wait = 20 * (attempt + 1)
                    print(f"Rate limited. Waiting {wait}s before retry...")
                    time.sleep(wait)
                else:
                    answer = f"Error generating answer: {error}"
                    break

        sources = self._extract_sources(context_chunks)
        return {"answer": answer, "sources": sources}