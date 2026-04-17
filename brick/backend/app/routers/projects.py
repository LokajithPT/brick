import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/api/projects")

try:
    from app.services.project_store import PROJECT_STORE
except Exception as e:
    logging.error(f"Failed to import PROJECT_STORE: {e}")
    PROJECT_STORE = None


class CreateProjectRequest(BaseModel):
    name: str


@router.post("/")
async def create_project(request: CreateProjectRequest):
    if PROJECT_STORE is None:
        raise HTTPException(status_code=500, detail="Project store not initialized")
    try:
        project = PROJECT_STORE.create_project(request.name)
        return {"success": True, "project": project}
    except Exception as e:
        logging.error(f"Create project error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_projects():
    if PROJECT_STORE is None:
        raise HTTPException(status_code=500, detail="Project store not initialized")
    try:
        projects = PROJECT_STORE.list_projects()
        return {"projects": projects, "total": len(projects)}
    except Exception as e:
        logging.error(f"List projects error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project(project_id: str):
    if PROJECT_STORE is None:
        raise HTTPException(status_code=500, detail="Project store not initialized")
    try:
        project = PROJECT_STORE.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        logging.error(f"Get project error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    if PROJECT_STORE is None:
        raise HTTPException(status_code=500, detail="Project store not initialized")
    try:
        success = PROJECT_STORE.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        return {"success": True, "message": "Project deleted"}
    except Exception as e:
        logging.error(f"Delete project error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/documents")
async def get_project_documents(project_id: str):
    if PROJECT_STORE is None:
        raise HTTPException(status_code=500, detail="Project store not initialized")
    try:
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
    except Exception as e:
        logging.error(f"Get project docs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
