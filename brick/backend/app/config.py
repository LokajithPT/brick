import os
from pathlib import Path

if os.environ.get("RENDER"):
    BASE_DIR = Path("/opt/render/project/src")
else:
    BASE_DIR = Path(__file__).parent.parent.parent.parent

DOCUMENTS_DIR = BASE_DIR / "documents"
ASSETS_DIR = BASE_DIR / "assets"
PROJECTS_DIR = BASE_DIR / "projects"

DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
