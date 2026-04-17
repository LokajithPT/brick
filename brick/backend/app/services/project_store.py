import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from app.config import BASE_DIR


class ProjectStore:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else BASE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir = self.base_dir / "projects"
        self.projects_dir.mkdir(exist_ok=True)
        self.index_file = self.base_dir / "projects_index.json"
        self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            with open(self.index_file) as f:
                self.index = json.load(f)
        else:
            self.index = {"projects": {}}

    def _save_index(self):
        with open(self.index_file, "w") as f:
            json.dump(self.index, f, indent=2)

    def create_project(self, name: str) -> dict:
        project_id = str(uuid.uuid4())[:8]
        project_dir = self.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        project_info = {
            "id": project_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "documents": [],
            "status": "active",
        }

        self.index["projects"][project_id] = project_info
        self._save_index()

        return project_info

    def get_project(self, project_id: str) -> dict:
        return self.index["projects"].get(project_id)

    def list_projects(self) -> list:
        return list(self.index["projects"].values())

    def delete_project(self, project_id: str) -> bool:
        if project_id in self.index["projects"]:
            project_dir = self.projects_dir / project_id
            if project_dir.exists():
                import shutil

                shutil.rmtree(project_dir)
            del self.index["projects"][project_id]
            self._save_index()
            return True
        return False

    def add_document_to_project(self, project_id: str, doc_id: str) -> bool:
        if project_id in self.index["projects"]:
            if doc_id not in self.index["projects"][project_id]["documents"]:
                self.index["projects"][project_id]["documents"].append(doc_id)
                self._save_index()
            return True
        return False

    def remove_document_from_project(self, project_id: str, doc_id: str) -> bool:
        if project_id in self.index["projects"]:
            if doc_id in self.index["projects"][project_id]["documents"]:
                self.index["projects"][project_id]["documents"].remove(doc_id)
                self._save_index()
            return True
        return False

    def get_project_documents(self, project_id: str) -> list:
        project = self.get_project(project_id)
        if project:
            return project.get("documents", [])
        return []


PROJECT_STORE = ProjectStore()
