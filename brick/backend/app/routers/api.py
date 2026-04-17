from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest
from app.services.query import QueryService

router = APIRouter(prefix="/api")
query_service = QueryService()


@router.post("/query")
async def query_documents(request: QueryRequest):
    try:
        result = await query_service.query(
            question=request.question, project_id=request.project_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/index/{namespace}")
async def get_document_index(namespace: str):
    if namespace not in query_service.documents:
        raise HTTPException(status_code=404, detail="Document not found")

    index = query_service.documents[namespace]
    pages = index.get("pages", {})

    sections = {
        "Kitchen": [],
        "Bathroom": [],
        "Living Room": [],
        "Bedroom": [],
        "Dining": [],
        "Lighting": [],
        "Flooring": [],
        "Exterior": [],
        "Other": [],
    }

    keywords = {
        "Kitchen": [
            "kitchen",
            "range",
            "hood",
            "cabinet",
            "fridge",
            "dishwasher",
            "pantry",
        ],
        "Bathroom": [
            "bath",
            "shower",
            "sink",
            "toilet",
            "vanity",
            "water closet",
            "powder",
        ],
        "Living Room": ["living room", "great room", "fireplace", "den"],
        "Bedroom": ["bedroom", "closet", "master"],
        "Dining": ["dining", "bar", "breakfast"],
        "Lighting": ["lighting", "fixture", "light"],
        "Flooring": ["floor", "flooring", "tile", "wood"],
        "Exterior": ["exterior", "outdoor", "patio", "pool", "bbq", "fireplace"],
    }

    for page_num_str, page_data in pages.items():
        page_num = int(page_num_str)
        text = page_data.get("text_preview", "").lower()

        for section, kws in keywords.items():
            if any(kw in text for kw in kws):
                sections[section].append(
                    {
                        "page": page_num,
                        "title": page_data.get("text_preview", "")[:80],
                        "image": page_data.get("image_url"),
                    }
                )
                break
        else:
            sections["Other"].append(
                {
                    "page": page_num,
                    "title": page_data.get("text_preview", "")[:80],
                    "image": page_data.get("image_url"),
                }
            )

    return {
        "namespace": namespace,
        "total_pages": index.get("total_pages", 0),
        "sections": {k: v for k, v in sections.items() if v},
    }


@router.get("/documents")
async def list_documents():
    docs = []
    for namespace, data in query_service.documents.items():
        docs.append(
            {
                "id": namespace,
                "name": namespace.replace("_", " ").title(),
                "namespace": namespace,
                "page_count": data.get("total_pages", 0),
            }
        )
    return docs


@router.get("/documents/{namespace}")
async def get_document(namespace: str):
    if namespace not in query_service.documents:
        raise HTTPException(status_code=404, detail="Document not found")
    return query_service.documents[namespace]


@router.get("/documents/{namespace}/page/{page_num}")
async def get_page(namespace: str, page_num: int):
    if namespace not in query_service.documents:
        raise HTTPException(status_code=404, detail="Document not found")

    pages = query_service.documents[namespace].get("pages", {})
    page_key = str(page_num)

    if page_key not in pages:
        raise HTTPException(status_code=404, detail="Page not found")

    return pages[page_key]
