import os
import json
from dotenv import load_dotenv
from app.config import ASSETS_DIR

load_dotenv()


class SearchService:
    def __init__(self):
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

    def search(self, query: str, top_k: int = 10):
        query_terms = [t.lower() for t in query.replace("?", "").split() if len(t) > 2]
        results = []

        for namespace, doc in self.documents.items():
            for page_num_str, page_data in doc["pages"].items():
                page_num = int(page_num_str)
                text = page_data.get("text_preview", "").lower()
                text_len = page_data.get("text_length", 0)

                score = 0
                matched_terms = []

                for term in query_terms:
                    if term in text:
                        score += 10
                        matched_terms.append(term)
                    if term in text[:200]:
                        score += 5

                # Boost score for pages with more content
                if text_len > 200:
                    score += text_len / 100
                elif text_len < 100:
                    score *= 0.5

                # Boost for title-like pages (short text but keywords)
                if text_len < 150 and any(
                    kw in text for kw in ["spec", "plan", "view", "sheet", "drawing"]
                ):
                    score += 5

                if score > 5:
                    results.append(
                        {
                            "namespace": namespace,
                            "page": page_num,
                            "score": score,
                            "text": page_data.get("text_preview", ""),
                            "text_len": text_len,
                            "image_url": page_data.get("image_url"),
                            "matched": matched_terms,
                        }
                    )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_answer_context(self, results):
        context = []
        for r in results[:5]:
            context.append(f"""Page {r["page"]} ({r["namespace"]}):
{r["text"][:500]}
[Image: {r["image_url"]}]""")
        return "\n---\n".join(context)


def get_search_results(query):
    service = SearchService()
    results = service.search(query)

    print(f"\nQuery: {query}")
    print(f"Found {len(results)} relevant pages\n")

    for r in results[:5]:
        print(f"Page {r['page']} ({r['namespace']}) - Score: {r['score']:.1f}")
        print(f"  {r['text'][:150]}...")
        print()

    return results
