import os
import json
import time
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SCRIPT_DIR = Path(__file__).parent.parent.parent
LLAMA_API_KEY = os.getenv("LLAMAPARSE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.1-8b-instant"
ASSETS_DIR = SCRIPT_DIR / "assets"
PDF_DIR = SCRIPT_DIR.parent


async def parse_with_llamaparse(pdf_path: str, namespace: str) -> dict:
    print(f"Parsing {pdf_path} with LlamaParse...")

    with open(pdf_path, "rb") as f:
        files = {"file": (os.path.basename(pdf_path), f.read(), "application/pdf")}
        data = {"namespace": namespace}
        headers = {"Authorization": f"Bearer {LLAMA_API_KEY}"}

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                "https://cloud.llamaindex.ai/api/parsing/upload",
                headers=headers,
                data=data,
                files=files,
            )

    if response.status_code != 200:
        print(f"LlamaParse error: {response.text}")
        return None

    result = response.json()
    job_id = result.get("job_id")
    print(f"Job ID: {job_id}")

    print("Waiting for parsing to complete...")
    for i in range(60):
        async with httpx.AsyncClient(timeout=30) as client:
            status_response = await client.get(
                f"https://cloud.llamaindex.ai/api/parsing/job/{job_id}",
                headers=headers,
            )

        status = status_response.json()
        state = status.get("status", status.get("state", "unknown"))
        print(f"  Status: {state}")

        if state == "success":
            print("Parsing complete!")

            content_response = await client.get(
                f"https://cloud.llamaindex.ai/api/parsing/job/{job_id}/content/markdown",
                headers=headers,
            )

            return content_response.json()

        if state in ["error", "failed"]:
            print(f"Parsing failed: {status}")
            return None

        time.sleep(5)

    return None


async def analyze_page_with_ai(
    page_content: str, page_num: int, namespace: str
) -> dict:
    prompt = f"""Analyze this architectural document page and extract key information.

DOCUMENT: {namespace}
PAGE CONTENT:
{page_content[:2000]}

Extract and return valid JSON with:
{{
  "title": "What is this page about (e.g., 'Primary Bath Specs', 'Kitchen Plan View')",
  "room": "Which room/area (e.g., 'Kitchen', 'Primary Bath', 'Living Room', 'Exterior', 'General')",
  "category": "Type of content (e.g., 'plan view', 'spec sheet', 'shop drawing', 'render', 'finish schedule', 'table of contents')",
  "items": ["list", "of", "specific", "items", "fixtures", "materials", "models", "mentioned"],
  "keywords": ["5-10", "relevant", "keywords", "for", "searching"],
  "summary": "Brief 1-2 sentence summary"
}}

Return ONLY valid JSON, no markdown code blocks."""

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

        content = response.json()["choices"][0]["message"]["content"]

        try:
            result = json.loads(content.strip())
            return result
        except:
            return {
                "title": f"Page {page_num}",
                "room": "Unknown",
                "category": "Unknown",
                "items": [],
                "keywords": [],
                "summary": page_content[:200] if page_content else "No content",
            }


async def process_pdfs():
    files = [
        ("Marlette Permit Set 8.20.2025.pdf", "permit_set"),
        ("MARLETTE_WORKING DESIGN BOOK_02.16.2026.pdf", "working_design_book"),
    ]

    all_data = {}

    for filename, namespace in files:
        pdf_path = os.path.join(PDF_DIR, filename)
        output_path = os.path.join(ASSETS_DIR, f"{namespace}_llamaparse.json")

        if os.path.exists(output_path):
            print(f"\nLoading cached LlamaParse data for {namespace}...")
            with open(output_path) as f:
                parsed_data = json.load(f)
        else:
            print(f"\n{'=' * 60}")
            print(f"Processing: {filename}")
            print(f"{'=' * 60}")

            parsed_data = await parse_with_llamaparse(pdf_path, namespace)

            if parsed_data:
                with open(output_path, "w") as f:
                    json.dump(parsed_data, f, indent=2)
                print(f"Saved to {output_path}")

        if parsed_data:
            all_data[namespace] = parsed_data

    print("\n" + "=" * 60)
    print("Analyzing pages with AI...")
    print("=" * 60)

    ai_index = {"pages": {}}

    for namespace, parsed_data in all_data.items():
        markdown = parsed_data.get("markdown", "")

        pages = markdown.split("## Page")

        for i, page_content in enumerate(pages[1:], 1):
            page_num = i
            title = (
                page_content.split("\n")[0].strip() if page_content else str(page_num)
            )

            print(f"Analyzing page {page_num} for {namespace}...")

            result = await analyze_page_with_ai(page_content, page_num, namespace)

            ai_index["pages"][f"{namespace}_p{page_num}"] = {
                **result,
                "page_num": page_num,
                "namespace": namespace,
                "preview": page_content[:300].strip(),
            }

            time.sleep(0.3)

            if i % 20 == 0:
                with open(os.path.join(ASSETS_DIR, "ai_index.json"), "w") as f:
                    json.dump(ai_index, f, indent=2)
                print(f"Saved progress: {i} pages analyzed")

    final_path = os.path.join(ASSETS_DIR, "ai_index.json")
    with open(final_path, "w") as f:
        json.dump(ai_index, f, indent=2)

    print(f"\nDone! Final index saved to {final_path}")
    print(f"Total pages analyzed: {len(ai_index['pages'])}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(process_pdfs())
