import os
from pathlib import Path

if "render" in os.environ.get("HOSTNAME", "").lower():
    BASE_DIR = Path("/opt/render/project/src")
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

DOCUMENTS_DIR = BASE_DIR / "documents"
ASSETS_DIR = BASE_DIR / "assets"
PROJECTS_DIR = BASE_DIR / "projects"

for d in [BASE_DIR, DOCUMENTS_DIR, ASSETS_DIR, PROJECTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
