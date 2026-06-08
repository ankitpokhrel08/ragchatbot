import os
import requests
from ragchatbot.llm.base import BaseLLM
from typing import Generator


class OllamaLLM(BaseLLM):
    """Ollama local LLM adapter."""

    def __init__(self, model: str = None, host: str = "http://localhost:11434"):
        self.model = model or os.getenv("ragchatbot_MODEL", "llama3.2")
        self.host = host
        self._verify_connection()

    def _verify_connection(self):
        """Check Ollama server is running."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=3)
            response.raise_for_status()
            print(f"Ollama ready — model: {self.model}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Ollama server not running. Start it with: ollama serve"
            )
        except Exception as e:
            raise ConnectionError(f"Ollama connection failed: {str(e)}")

    def generate(self, question: str, context_chunks: list[dict]) -> dict:
        if not context_chunks:
            return {
                "answer": "I don't have that information in my docs.",
                "sources": []
            }

        prompt = self._build_prompt(question, context_chunks)

        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            answer = response.json()["response"].strip()

        except requests.exceptions.Timeout:
            answer = "Error: Ollama timed out. Model may still be loading."
        except Exception as e:
            answer = f"Error generating answer: {str(e)}"

        sources = self._extract_sources(context_chunks)
        return {"answer": answer, "sources": sources}
    
    def generate_stream(self, question: str, context_chunks: list[dict]) -> Generator:
        """Stream answer tokens from Ollama."""
        if not context_chunks:
            yield "I don't have that information in my docs."
            return

        prompt = self._build_prompt(question, context_chunks)

        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True,
                timeout=120
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        yield token
                    if data.get("done", False):
                        break

        except requests.exceptions.Timeout:
            yield "❌ Ollama timed out. Model may still be loading."
        except Exception as e:
            yield f"❌ Ollama streaming error: {str(e)}"