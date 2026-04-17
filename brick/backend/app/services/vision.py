import os
import base64
import httpx
from dotenv import load_dotenv
from app.config import ASSETS_DIR

load_dotenv()
IMAGE_BASE_URL = "http://localhost:8000"


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


async def analyze_image(image_url: str, question: str = None) -> dict:
    image_path = os.path.join(ASSETS_DIR, image_url.replace("/images/", ""))

    if not os.path.exists(image_path):
        return {"error": "Image not found"}

    image_data = encode_image(image_path)

    prompt = """Analyze this architectural document page. Extract and return valid JSON:
{
  "title": "brief title of what's on this page",
  "room": "which room/area",
  "specs": ["list of specific specs, models, dimensions, materials found"],
  "dimensions": ["any measurements mentioned"],
  "summary": "2 sentence summary of content"
}

Return ONLY valid JSON, no markdown."""

    if question:
        prompt = f"""Look at this architectural document image and answer: {question}

Return your answer as JSON:
{{"answer": "your answer here", "specs": ["specs mentioned"], "dimensions": ["dimensions mentioned"]}}

Return ONLY valid JSON."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/png", "data": image_data}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        return {"error": f"API error: {response.status_code}"}

    data = response.json()

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        return {"error": str(e), "raw": data}


async def analyze_images_for_answer(image_urls: list, question: str) -> dict:
    all_results = []

    for img_url in image_urls[:3]:
        print(f"Analyzing: {img_url}")
        result = await analyze_image(img_url, question)
        result["image_url"] = img_url
        all_results.append(result)

        if len(all_results) >= 2:
            break

    return {"analyses": all_results, "question": question}
