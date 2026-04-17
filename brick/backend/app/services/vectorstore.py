import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()


class VectorStore:
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not set")
        self.client = Pinecone(api_key=self.api_key)

    async def search(self, query: str, namespace: str, top_k: int) -> list[dict]:
        return [
            {
                "page": 42,
                "text": "Sample extracted text from document...",
                "image_url": None,
                "score": 0.95,
            }
        ]

    async def upsert(self, vectors: list[dict], namespace: str):
        pass
