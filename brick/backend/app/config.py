import os
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
BASE_DIR = THIS_FILE.parent.parent.parent
if not BASE_DIR.exists():
    BASE_DIR = Path("/opt/render/project/src")

DOCUMENTS_DIR = BASE_DIR / "documents"
ASSETS_DIR = BASE_DIR.parent / "assets"
PROJECTS_DIR = BASE_DIR.parent / "projects"
