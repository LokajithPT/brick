import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.routers.api import router as api_router
from app.routers.documents import router as documents_router
from app.routers.projects import router as projects_router

try:
    from app.config import BASE_DIR, ASSETS_DIR, DOCUMENTS_DIR

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    (DOCUMENTS_DIR).mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "projects").mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Config import failed: {e}")
    BASE_DIR = Path(__file__).parent.parent.parent
    DOCUMENTS_DIR = BASE_DIR / "documents"
    ASSETS_DIR = BASE_DIR / "assets"

app = FastAPI(title="BRICK API")
app.include_router(api_router)
app.include_router(documents_router)
app.include_router(projects_router)

origins_env = os.getenv("CORS_ORIGINS", "")
origins = (
    [o.strip() for o in origins_env.split(",") if o.strip()]
    if origins_env
    else ["http://localhost:3000"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"] if "*" in origins else origins,
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
