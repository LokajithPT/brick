import sys
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

print(f"Python: {sys.version}", flush=True)
print(f"CWD: {os.getcwd()}", flush=True)

THIS_DIR = Path(__file__).resolve().parent
BASE_DIR = THIS_DIR.parent.parent
DOCS_DIR = BASE_DIR / "documents"
ASSETS_DIR = BASE_DIR.parent / "assets"

print(f"BASE_DIR: {BASE_DIR}", flush=True)
print(f"DOCS_DIR: {DOCS_DIR}", flush=True)

try:
    from app.routers.api import router as api_router
    from app.routers.documents import router as documents_router
    from app.routers.projects import router as projects_router

    print("All routers imported", flush=True)
except Exception as e:
    print(f"Router import error: {e}", flush=True)
    api_router = None
    documents_router = None
    projects_router = None

app = FastAPI(title="BRICK API")

if api_router:
    app.include_router(api_router)
if documents_router:
    app.include_router(documents_router)
if projects_router:
    app.include_router(projects_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "BRICK API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
