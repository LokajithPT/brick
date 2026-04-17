from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import json
from app.services.document_store import DOCUMENT_STORE
from app.services.pdf_parser import parse_pdf_to_index, search_pages
from app.services.project_store import PROJECT_STORE

router = APIRouter(prefix="/api/docs")


class ParseRequest(BaseModel):
    doc_id: str


def parse_document_task(doc_id: str):
    doc = DOCUMENT_STORE.get_document(doc_id)
    if not doc:
        return

    output_dir = DOCUMENT_STORE.get_parsed_path(doc_id)
    os.makedirs(output_dir, exist_ok=True)

    def progress_callback(doc_id, current_page, total_pages, status):
        progress_data = {
            "current_page": current_page,
            "total_pages": total_pages,
            "percentage": int((current_page / total_pages) * 100)
            if total_pages > 0
            else 0,
            "status": status,
        }
        DOCUMENT_STORE.update_document(doc_id, {"progress": progress_data})

    try:
        DOCUMENT_STORE.update_document(
            doc_id,
            {
                "status": "parsing",
                "parsed_path": str(output_dir),
                "progress": {
                    "current_page": 0,
                    "total_pages": 0,
                    "percentage": 0,
                    "status": "starting",
                },
            },
        )

        index_data = parse_pdf_to_index(
            doc["upload_path"],
            str(output_dir),
            doc_id,
            progress_callback=progress_callback,
        )

        DOCUMENT_STORE.update_document(
            doc_id,
            {
                "status": "parsed",
                "parsed_path": str(output_dir),
                "index_path": str(output_dir / "index.json"),
                "page_count": index_data["total_pages"],
                "parsed_at": str(os.times()),
            },
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        DOCUMENT_STORE.update_document(doc_id, {"status": "error", "error": str(e)})


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...), project_id: Optional[str] = Form(None)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    if project_id:
        project = PROJECT_STORE.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    doc_info = DOCUMENT_STORE.add_document(file.filename, content)

    if project_id:
        PROJECT_STORE.add_document_to_project(project_id, doc_info["id"])
        doc_info["project_id"] = project_id

    return {"success": True, "document": doc_info}


@router.get("/")
async def list_documents():
    docs = DOCUMENT_STORE.list_documents()
    return {"documents": docs, "total": len(docs)}


@router.get("/{doc_id}")
async def get_document(doc_id: str):
    doc = DOCUMENT_STORE.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/{doc_id}/parse")
async def parse_document(doc_id: str, background_tasks: BackgroundTasks):
    doc = DOCUMENT_STORE.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc["status"] == "parsed":
        return {"success": True, "message": "Already parsed", "status": "parsed"}

    background_tasks.add_task(parse_document_task, doc_id)

    return {"success": True, "message": "Parsing started", "status": "parsing"}


@router.get("/{doc_id}/status")
async def get_document_status(doc_id: str):
    doc = DOCUMENT_STORE.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    progress = doc.get("progress", {})

    return {
        "id": doc["id"],
        "filename": doc["filename"],
        "status": doc["status"],
        "page_count": doc.get("page_count", 0),
        "progress": progress,
    }


@router.get("/{doc_id}/progress")
async def get_parsing_progress_endpoint(doc_id: str):
    doc = DOCUMENT_STORE.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    progress = doc.get("progress", {})

    return {
        "doc_id": doc_id,
        "filename": doc["filename"],
        "status": doc["status"],
        **progress,
    }


@router.get("/{doc_id}/index")
async def get_document_index(doc_id: str):
    doc = DOCUMENT_STORE.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc["status"] != "parsed":
        raise HTTPException(status_code=400, detail="Document not parsed yet")

    index_path = os.path.join(doc["parsed_path"], "index.json")
    with open(index_path) as f:
        index_data = json.load(f)

    sections = categorize_pages(index_data)

    return {
        "id": doc_id,
        "filename": doc["filename"],
        "page_count": doc["page_count"],
        "sections": sections,
    }


def categorize_pages(index_data: dict) -> dict:
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
            "microwave",
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

    for page_num_str, page_data in index_data["pages"].items():
        page_num = int(page_num_str)
        text = page_data.get("text_preview", "").lower()

        categorized = False
        for section, kws in keywords.items():
            if any(kw in text for kw in kws):
                sections[section].append(
                    {
                        "page": page_num,
                        "image": page_data.get("image"),
                        "preview": page_data.get("text_preview", "")[:80],
                    }
                )
                categorized = True
                break

        if not categorized:
            sections["Other"].append(
                {
                    "page": page_num,
                    "image": page_data.get("image"),
                    "preview": page_data.get("text_preview", "")[:80],
                }
            )

    return {k: v for k, v in sections.items() if v}


@router.get("/{doc_id}/image/{page_num}")
async def get_page_image(doc_id: str, page_num: int):
    doc = DOCUMENT_STORE.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    image_path = os.path.join(
        doc["parsed_path"], f"{doc['filename'].replace('.pdf', '')}_p{page_num}.png"
    )

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(image_path, media_type="image/png")


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    success = DOCUMENT_STORE.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"success": True, "message": "Document deleted"}
