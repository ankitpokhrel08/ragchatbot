import os
from dotenv import load_dotenv
from ragchatbot.llm.base import BaseLLM

load_dotenv()


class OpenAILLM(BaseLLM):
    """OpenAI LLM adapter."""

    def __init__(self, api_key: str = None, model: str = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "❌ openai package not installed.\n"
                "   Run: pip install openai"
            )

        key = api_key or os.getenv("OPENAI_API_KEY")
        model = model or os.getenv("ragchatbot_MODEL", "gpt-4o-mini")

        if not key:
            raise ValueError(
                "❌ OpenAI API key not found.\n"
                "   Set OPENAI_API_KEY in your .env file or pass api_key= directly.\n"
                "   Get a key at: https://platform.openai.com/api-keys"
            )

        self.client = OpenAI(api_key=key)
        self.model = model
        print(f"OpenAI ready — model: {model}")

    def generate(self, question: str, context_chunks: list[dict]) -> dict:
        if not context_chunks:
            return {
                "answer": "I don't have that information in my docs.",
                "sources": []
            }

        prompt = self._build_prompt(question, context_chunks)
        sources = self._extract_sources(context_chunks)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            answer = response.choices[0].message.content.strip()

        except Exception as e:
            error = str(e)
            if "401" in error:
                answer = "❌ OpenAI API key invalid. Check OPENAI_API_KEY in .env"
            elif "429" in error:
                answer = "❌ OpenAI rate limit hit. Wait a moment and try again."
            elif "insufficient_quota" in error:
                answer = "❌ OpenAI quota exceeded. Check your billing at platform.openai.com"
            else:
                answer = f"❌ OpenAI error: {error}"

        return {"answer": answer, "sources": sources}