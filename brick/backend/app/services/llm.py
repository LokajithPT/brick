import os
import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "ollama")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    async def generate(self, question: str, context: list[dict]) -> str:
        context_text = "\n\n".join([c["text"] for c in context])

        prompt = f"""Based on the following context, answer the question. Always cite the page number.

Context:
{context_text}

Question: {question}

Answer:"""

        if self.provider == "ollama":
            return await self._ollama_generate(prompt)
        elif self.provider == "groq":
            return await self._groq_generate(prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def _ollama_generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json()["response"]

    async def _groq_generate(self, prompt: str) -> str:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set")

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
