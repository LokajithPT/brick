from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.project_store import PROJECT_STORE

router = APIRouter(prefix="/api/projects")


class CreateProjectRequest(BaseModel):
    name: str


@router.post("/")
async def create_project(request: CreateProjectRequest):
    project = PROJECT_STORE.create_project(request.name)
    return {"success": True, "project": project}


@router.get("/")
async def list_projects():
    projects = PROJECT_STORE.list_projects()
    return {"projects": projects, "total": len(projects)}


@router.get("/{project_id}")
async def get_project(project_id: str):
    project = PROJECT_STORE.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    success = PROJECT_STORE.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"success": True, "message": "Project deleted"}


@router.get("/{project_id}/documents")
async def get_project_documents(project_id: str):
    project = PROJECT_STORE.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.services.document_store import DOCUMENT_STORE

    docs = []
    for doc_id in project.get("documents", []):
        doc = DOCUMENT_STORE.get_document(doc_id)
        if doc:
            docs.append(doc)

    return {"documents": docs, "total": len(docs)}
