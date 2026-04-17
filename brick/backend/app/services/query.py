import os
import json
import httpx
from dotenv import load_dotenv
from app.config import ASSETS_DIR

load_dotenv()


class QueryService:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.assets_dir = ASSETS_DIR
        self.documents = self._load_documents()

    def _load_documents(self):
        docs = {}
        for namespace in ["permit_set", "working_design_book"]:
            index_path = os.path.join(self.assets_dir, f"{namespace}_index.json")
            if os.path.exists(index_path):
                with open(index_path) as f:
                    docs[namespace] = json.load(f)
        return docs

    def _load_project_documents(self, project_id: str):
        from app.services.document_store import DOCUMENT_STORE
        from app.services.project_store import PROJECT_STORE

        project = PROJECT_STORE.get_project(project_id)
        if not project:
            return {}

        docs = {}
        for doc_id in project.get("documents", []):
            doc = DOCUMENT_STORE.get_document(doc_id)
            if doc and doc.get("status") == "parsed":
                index_path = os.path.join(doc["parsed_path"], "index.json")
                if os.path.exists(index_path):
                    with open(index_path) as f:
                        index_data = json.load(f)
                    docs[doc_id] = index_data
        return docs

    def search(self, query: str, top_k: int = 10, project_id: str = None):
        query_terms = [t.lower() for t in query.replace("?", "").split() if len(t) > 2]
        results = []

        if project_id:
            documents = self._load_project_documents(project_id)
        else:
            documents = self.documents

        for namespace, doc in documents.items():
            for page_num_str, page_data in doc.get("pages", {}).items():
                page_num = int(page_num_str)
                text = page_data.get("text_preview", "").lower()
                text_len = page_data.get("text_length", 0)

                score = 0
                for term in query_terms:
                    if term in text:
                        score += 10
                    if term in text[:200]:
                        score += 5

                if text_len > 200:
                    score += text_len / 100
                elif text_len < 100:
                    score *= 0.5

                if score > 5:
                    results.append(
                        {
                            "namespace": namespace,
                            "page": page_num,
                            "score": score,
                            "text": page_data.get("text_preview", ""),
                            "image_url": page_data.get("image_url"),
                        }
                    )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def query(self, question: str, project_id: str = None) -> dict:
        results = self.search(question, project_id=project_id)

        if not results:
            return {
                "answer": "I couldn't find relevant information. Try browsing the Document Index.",
                "sources": [],
                "images": [],
            }

        context_parts = []
        for r in results[:5]:
            context_parts.append(f"""=== {r["namespace"]} - Page {r["page"]} ===
{r["text"][:800]}

Image: {r["image_url"] if r["image_url"] else "N/A"}""")

        context = "\n---\n".join(context_parts)

        prompt = f"""You are an expert assistant for the Marlette Residence architectural project.

Based on the document pages below, answer with SPECIFIC details including specs, materials, models, and any specifications mentioned.

DOCUMENT PAGES:
{context}

QUESTION: {question}

Provide a detailed answer with:
1. Specific specs, materials, models mentioned
2. Page number references
3. Any dimensions or measurements found

ANSWER:"""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                answer = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            answer = f"Error: {str(e)}"

        sources = [
            {"page": r["page"], "namespace": r["namespace"], "text": r["text"][:150]}
            for r in results[:5]
        ]
        images = [
            {"page": r["page"], "namespace": r["namespace"], "url": r["image_url"]}
            for r in results[:5]
            if r.get("image_url")
        ]

        return {
            "answer": answer,
            "sources": sources,
            "images": images,
        }
