import os
import json
import time
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = Path(__file__).parent.parent.parent
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"
ASSETS_DIR = SCRIPT_DIR / "assets"


async def analyze_page(
    text: str, page_num: int, namespace: str, retries: int = 3
) -> dict:
    prompt = f"""Analyze this architectural document page and extract key information.

DOCUMENT: {namespace}
PAGE: {page_num}

TEXT CONTENT:
{text[:1500]}

Extract and return valid JSON:
{{"title": "brief title", "room": "room name", "category": "plan view/spec sheet/etc", "items": ["item1", "item2"], "keywords": ["kw1", "kw2"], "summary": "2 sentence summary"}}

Return ONLY valid JSON, no markdown."""

    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": GROQ_MODEL,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                    },
                )

                if response.status_code != 200:
                    print(f"API error: {response.status_code}")
                    time.sleep(5)
                    continue

                data = response.json()
                if "choices" not in data:
                    print(f"No choices in response")
                    time.sleep(5)
                    continue

                content = data["choices"][0]["message"]["content"]

                try:
                    return json.loads(content.strip())
                except:
                    return {
                        "title": f"Page {page_num}",
                        "room": "Unknown",
                        "category": "Unknown",
                        "items": [],
                        "keywords": [],
                        "summary": text[:150] if text else "",
                    }
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(3)

    return {
        "title": f"Page {page_num}",
        "room": "Unknown",
        "category": "Unknown",
        "items": [],
        "keywords": [],
        "summary": text[:150] if text else "",
    }


async def main():
    output_path = os.path.join(ASSETS_DIR, "ai_index.json")

    if os.path.exists(output_path):
        with open(output_path) as f:
            all_pages = json.load(f).get("pages", {})
        print(f"Resuming with {len(all_pages)} pages already analyzed")
    else:
        all_pages = {}

    files = [
        ("permit_set", "Marlette Permit Set"),
        ("working_design_book", "Marlette Working Design Book"),
    ]

    for namespace, doc_name in files:
        index_path = os.path.join(ASSETS_DIR, f"{namespace}_index.json")

        if not os.path.exists(index_path):
            print(f"Missing index for {namespace}")
            continue

        with open(index_path) as f:
            index = json.load(f)

        print(f"\nAnalyzing: {doc_name} ({len(index['pages'])} pages)")

        for page_num_str, page_data in sorted(
            index["pages"].items(), key=lambda x: int(x[0])
        ):
            page_num = int(page_num_str)
            key = f"{namespace}_p{page_num}"

            if key in all_pages:
                continue

            text = page_data.get("text_preview", "")

            if not text or len(text) < 20:
                continue

            print(f"  Page {page_num}...", end=" ", flush=True)

            result = await analyze_page(text, page_num, namespace)

            all_pages[key] = {
                **result,
                "page_num": page_num,
                "namespace": namespace,
                "doc_name": doc_name,
                "text": text[:500],
                "image_url": page_data.get("image_url"),
            }

            print(f"✓ ({result['room']})")

            time.sleep(0.5)

            if len(all_pages) % 10 == 0:
                with open(output_path, "w") as f:
                    json.dump(
                        {"pages": all_pages, "total": len(all_pages)}, f, indent=2
                    )

    with open(output_path, "w") as f:
        json.dump({"pages": all_pages, "total": len(all_pages)}, f, indent=2)

    print(f"\nDONE! Analyzed {len(all_pages)} pages")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
