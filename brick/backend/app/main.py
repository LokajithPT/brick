import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

THIS_DIR = Path(__file__).resolve().parent
BASE_DIR = THIS_DIR.parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
ASSETS_DIR = BASE_DIR / "assets"

for d in [BASE_DIR, DOCUMENTS_DIR, ASSETS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="BRICK API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from app.routers.api import router as api_router

    app.include_router(api_router)
except Exception as e:
    print(f"Failed to load api router: {e}")

try:
    from app.routers.documents import router as documents_router

    app.include_router(documents_router)
except Exception as e:
    print(f"Failed to load documents router: {e}")

try:
    from app.routers.projects import router as projects_router

    app.include_router(projects_router)
except Exception as e:
    print(f"Failed to load projects router: {e}")


@app.get("/images/{path:path}")
async def get_image(path: str):
    for base in [ASSETS_DIR, DOCUMENTS_DIR]:
        image_path = os.path.join(base, path)
        if os.path.exists(image_path):
            return FileResponse(image_path)
    return {"error": "Image not found"}


@app.get("/")
def root():
    return {"status": "ok", "service": "BRICK API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
