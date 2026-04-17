import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.routers.api import router as api_router
from app.routers.documents import router as documents_router
from app.routers.projects import router as projects_router
from app.config import ASSETS_DIR, DOCUMENTS_DIR

app = FastAPI(title="BRICK API")
app.include_router(api_router)
app.include_router(documents_router)
app.include_router(projects_router)

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/images/{path:path}")
async def get_image(path: str):
    for base in [ASSETS_DIR, DOCUMENTS_DIR]:
        image_path = os.path.join(base, path)
        if os.path.exists(image_path):
            return FileResponse(image_path)
    return {"error": "Image not found"}


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "BRICK API",
        "docs": "/api/docs",
        "query": "POST /api/query",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
